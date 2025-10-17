from __future__ import annotations

import asyncio
import threading
import base64
import logging
import os
from contextlib import asynccontextmanager
from random import random
from typing import Any, AsyncIterator, Dict, Iterable, Iterator, Optional, Sequence, Tuple

import orjson
from langgraph.checkpoint.serde.types import ChannelProtocol

import httpx
from langchain_core.runnables import RunnableConfig

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    get_checkpoint_id,
    get_checkpoint_metadata,
)
from langgraph.checkpoint.serde.base import SerializerProtocol
from langgraph.checkpoint.serde.encrypted import EncryptedSerializer

from .serde import Serializer
from agent_lab_sdk.metrics import get_metric

__all__ = ["AsyncAGWCheckpointSaver"]

logger = logging.getLogger(__name__)

AGW_METRIC_LABELS = ["method", "endpoint"]
AGW_HTTP_SUCCESS = get_metric(
    "counter",
    "agw_http_success_total",
    "Number of successful AGW HTTP requests",
    labelnames=AGW_METRIC_LABELS,
)
AGW_HTTP_ERROR = get_metric(
    "counter",
    "agw_http_error_total",
    "Number of failed AGW HTTP request attempts",
    labelnames=AGW_METRIC_LABELS,
)
AGW_HTTP_FINAL_ERROR = get_metric(
    "counter",
    "agw_http_final_error_total",
    "Number of AGW HTTP requests that failed after retries",
    labelnames=AGW_METRIC_LABELS,
)

TYPED_KEYS = ("type", "blob")


def _b64decode_strict(value: str) -> bytes | None:
    try:
        return base64.b64decode(value, validate=True)
    except Exception:
        return None

# ------------------------------------------------------------------ #
# helpers for Py < 3.10
# ------------------------------------------------------------------ #
try:
    anext  # type: ignore[name-defined]
except NameError:  # pragma: no cover

    async def anext(it):
        return await it.__anext__()


class AsyncAGWCheckpointSaver(BaseCheckpointSaver):
    """Persist checkpoints in Agent-Gateway с помощью `httpx` async client."""

    # ---------------------------- init / ctx -------------------------
    def __init__(
        self,
        base_url: str = "http://localhost",
        *,
        serde: SerializerProtocol | None = None,
        timeout: int | float = 10,
        api_key: str | None = None,
        extra_headers: Dict[str, str] | None = None,
        verify: bool = True,
    ):
        if not serde:
            base_serde: SerializerProtocol = Serializer()
            aes_key = (
                os.getenv("LANGGRAPH_AES_KEY")
                or os.getenv("AGW_AES_KEY")
                or os.getenv("AES_KEY")
            )
            if aes_key:
                base_serde = EncryptedSerializer.from_pycryptodome_aes(
                    base_serde, key=aes_key
                )
            serde = base_serde
        super().__init__(serde=serde)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        # Фоновый loop для sync-обёрток
        self._bg_loop: asyncio.AbstractEventLoop | None = None
        self._bg_thread: threading.Thread | None = None
        self._loop_lock = threading.Lock()

        raw_attempts = os.getenv("AGW_HTTP_MAX_RETRIES")
        if raw_attempts is None:
            self.retry_max_attempts = 3
        else:
            try:
                self.retry_max_attempts = max(int(raw_attempts), 1)
            except ValueError:
                logger.warning(
                    "Env %s expected int, got %r; using default %s",
                    "AGW_HTTP_MAX_RETRIES",
                    raw_attempts,
                    3,
                )
                self.retry_max_attempts = 3

        raw_backoff_base = os.getenv("AGW_HTTP_RETRY_BACKOFF_BASE")
        if raw_backoff_base is None:
            self.retry_backoff_base = 0.5
        else:
            try:
                self.retry_backoff_base = max(float(raw_backoff_base), 0.0)
            except ValueError:
                logger.warning(
                    "Env %s expected float, got %r; using default %.3f",
                    "AGW_HTTP_RETRY_BACKOFF_BASE",
                    raw_backoff_base,
                    0.5,
                )
                self.retry_backoff_base = 0.5

        raw_backoff_max = os.getenv("AGW_HTTP_RETRY_BACKOFF_MAX")
        if raw_backoff_max is None:
            self.retry_backoff_max = 5.0
        else:
            try:
                self.retry_backoff_max = max(float(raw_backoff_max), 0.0)
            except ValueError:
                logger.warning(
                    "Env %s expected float, got %r; using default %.3f",
                    "AGW_HTTP_RETRY_BACKOFF_MAX",
                    raw_backoff_max,
                    5.0,
                )
                self.retry_backoff_max = 5.0

        raw_jitter = os.getenv("AGW_HTTP_RETRY_JITTER")
        if raw_jitter is None:
            self.retry_jitter = 0.25
        else:
            try:
                self.retry_jitter = max(float(raw_jitter), 0.0)
            except ValueError:
                logger.warning(
                    "Env %s expected float, got %r; using default %.3f",
                    "AGW_HTTP_RETRY_JITTER",
                    raw_jitter,
                    0.25,
                )
                self.retry_jitter = 0.25

        self.headers: Dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if extra_headers:
            self.headers.update(extra_headers)
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

        self._verify = verify
        self._client: httpx.AsyncClient | None = None
        self._client_loop: asyncio.AbstractEventLoop | None = None

    def _create_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=self.timeout,
            verify=self._verify,
            trust_env=True,
        )

    def _ensure_bg_loop(self) -> asyncio.AbstractEventLoop:
        with self._loop_lock:
            if self._bg_loop and self._bg_loop.is_running():
                return self._bg_loop

            loop = asyncio.new_event_loop()

            def runner():
                asyncio.set_event_loop(loop)
                loop.run_forever()

            t = threading.Thread(target=runner, name="agw-checkpoint-loop", daemon=True)
            t.start()

            self._bg_loop = loop
            self._bg_thread = t
            return loop

    def _compute_retry_delay(self, attempt: int) -> float:
        if attempt <= 0:
            attempt = 1
        if self.retry_backoff_base <= 0:
            delay = 0.0
        else:
            delay = self.retry_backoff_base * (2 ** (attempt - 1))
            if self.retry_backoff_max > 0:
                delay = min(delay, self.retry_backoff_max)
        if self.retry_jitter > 0:
            delay += self.retry_jitter * random()
        return delay

    async def __aenter__(self):  # noqa: D401
        return self

    async def __aexit__(self, exc_type, exc, tb):  # noqa: D401
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception as close_exc:  # pragma: no cover - best effort
                logger.debug("Failed to close AGW httpx.AsyncClient: %s", close_exc)
            finally:
                self._client = None
                self._client_loop = None
        # останавливаем фоновый loop, если поднимали
        if self._bg_loop is not None:
            try:
                self._bg_loop.call_soon_threadsafe(self._bg_loop.stop)
            finally:
                self._bg_loop = None
                self._bg_thread = None

    # ----------------------- universal dump/load ---------------------
    def _safe_dump(self, obj: Any) -> Any:
        """
        JSON-first сериализация:
        1) Пытаемся через self.serde.dumps(obj).
           - Если вернул bytes: пробуем декодировать в JSON-строку и распарсить.
           - Если не JSON/не UTF-8 — заворачиваем как base64-строку.
           - Если вернул dict/list/scalar — они уже JSON-совместимы.
        2) Если self.serde.dumps(obj) бросает исключение (например, для Send),
           делаем типизированный фолбэк {"type": str, "blob": base64 | None}.
        """
        try:
            dumped = self.serde.dumps(obj)
        except Exception:
            # typed fallback (как рекомендуют в LangGraph для нетривиальных типов)
            # https://langchain-ai.github.io/langgraph/reference/checkpoints/
            try:
                t, b = self.serde.dumps_typed(obj)
            except Exception:
                # крайний случай: строковое представление
                t, b = type(obj).__name__, str(obj).encode()
            return {"type": t, "blob": base64.b64encode(b).decode() if b is not None else None}

        if isinstance(dumped, (bytes, bytearray)):
            try:
                s = dumped.decode()
                return orjson.loads(s)
            except (UnicodeDecodeError, orjson.JSONDecodeError):
                return base64.b64encode(dumped).decode()
        return dumped

    def _safe_load(self, obj: Any) -> Any:
        if obj is None:
            return None

        if isinstance(obj, dict):
            if all(k in obj for k in TYPED_KEYS):
                t = obj.get("type")
                blob = obj.get("blob")
                if blob is None:
                    try:
                        return self.serde.loads_typed((t, None))
                    except Exception:
                        return obj
                if isinstance(blob, str):
                    payload = _b64decode_strict(blob)
                    if payload is not None:
                        try:
                            return self.serde.loads_typed((t, payload))
                        except Exception:
                            # fall back to generic handling below
                            pass
            try:
                return self.serde.loads(orjson.dumps(obj))
            except Exception:
                return obj

        if isinstance(obj, (list, tuple)):
            if (
                len(obj) == 2
                and isinstance(obj[0], str)
                and (obj[1] is None or isinstance(obj[1], str))
            ):
                blob = obj[1]
                if blob is None:
                    try:
                        return self.serde.loads_typed((obj[0], None))
                    except Exception:
                        pass
                elif isinstance(blob, str):
                    payload = _b64decode_strict(blob)
                    if payload is not None:
                        try:
                            return self.serde.loads_typed((obj[0], payload))
                        except Exception:
                            pass
            try:
                return self.serde.loads(orjson.dumps(list(obj)))
            except Exception:
                return obj

        if isinstance(obj, str):
            try:
                return self.serde.loads(obj.encode())
            except Exception:
                payload = _b64decode_strict(obj)
                if payload is not None:
                    try:
                        return self.serde.loads(payload)
                    except Exception:
                        pass
                return obj

        try:
            return self.serde.loads(obj)
        except Exception:
            return obj

    # ----------------------- deep dump/load (leaf-first) -------------
    @staticmethod
    def _is_json_scalar(x: Any) -> bool:
        return x is None or isinstance(x, (str, int, float, bool))

    @staticmethod
    def _coerce_key(k: Any) -> str:
        return k if isinstance(k, str) else str(k)

    def _safe_dump_deep(self, obj: Any, _seen: set[int] | None = None) -> Any:
        """
        Идём от листьев к корню:
        - Для контейнеров рекурсируем внутрь и сохраняем форму контейнера.
        - Для листьев вызываем _safe_dump (fallback на serde/typed + base64).
        """
        if _seen is None:
            _seen = set()

        if self._is_json_scalar(obj):
            return obj

        if isinstance(obj, dict):
            oid = id(obj)
            if oid in _seen:
                return {"type": "Cycle", "blob": None}
            _seen.add(oid)
            return {
                self._coerce_key(k): self._safe_dump_deep(v, _seen) for k, v in obj.items()
            }

        if isinstance(obj, (list, tuple, set)):
            oid = id(obj)
            if oid in _seen:
                return ["<cycle>"]
            _seen.add(oid)
            return [self._safe_dump_deep(v, _seen) for v in obj]

        # лист: доверяем универсальному дамперу
        return self._safe_dump(obj)

    def _safe_load_deep(self, obj: Any, _seen: set[int] | None = None) -> Any:
        """
        Обратная операция:
        - Контейнеры сначала пробуем целиком скормить serde.loads(...).
          Если вернулся НЕ JSON-контейнер (например, объект сообщения) — возвращаем его.
          Иначе рекурсивно обходим внутрь и листья скармливаем _safe_load.
        - typed {"type","blob"} обрабатываем как раньше.
        """
        if _seen is None:
            _seen = set()

        # Примитивы: просто через _safe_load (декод base64/bytes и т.п.)
        if self._is_json_scalar(obj):
            return self._safe_load(obj)

        # dict
        if isinstance(obj, dict):
            # типизированная обёртка — сразу разворачиваем
            if all(k in obj for k in TYPED_KEYS):
                return self._safe_load(obj)

            # 1) parse-first: пробуем целиком восстановить объект через serde
            try:
                parsed = self.serde.loads(orjson.dumps(obj))
                # если получили не-JSON-контейнер (объект), возвращаем
                if not isinstance(parsed, (dict, list, tuple, str, int, float, bool, type(None))):
                    return parsed
            except Exception:
                pass

            # 2) иначе — рекурсивно
            oid = id(obj)
            if oid in _seen:
                return obj
            _seen.add(oid)
            return {k: self._safe_load_deep(v, _seen) for k, v in obj.items()}

        # list
        if isinstance(obj, list):
            # parse-first: пытаемся восстановить весь список одной операцией
            try:
                parsed = self.serde.loads(orjson.dumps(obj))
                if not isinstance(parsed, (dict, list, tuple, str, int, float, bool, type(None))):
                    return parsed
            except Exception:
                pass

            oid = id(obj)
            if oid in _seen:
                return obj
            _seen.add(oid)
            return [self._safe_load_deep(v, _seen) for v in obj]

        # tuple — аналогично list, но вернём list (JSON-совместимо)
        if isinstance(obj, tuple):
            try:
                parsed = self.serde.loads(orjson.dumps(obj))
                if not isinstance(parsed, (dict, list, tuple, str, int, float, bool, type(None))):
                    return parsed
            except Exception:
                pass

            oid = id(obj)
            if oid in _seen:
                return obj
            _seen.add(oid)
            return [self._safe_load_deep(v, _seen) for v in obj]

        # Всё остальное — лист, через _safe_load
        return self._safe_load(obj)

    # ----------------------- config <-> api --------------------------
    def _to_api_config(self, cfg: RunnableConfig | None) -> Dict[str, Any]:
        if not cfg:
            return {}
        c = cfg.get("configurable", {})
        res: Dict[str, Any] = {
            "threadId": c.get("thread_id", ""),
            "checkpointNs": c.get("checkpoint_ns", ""),
        }
        if cid := c.get("checkpoint_id"):
            res["checkpointId"] = cid
        if ts := c.get("thread_ts"):
            res["threadTs"] = ts
        return res

    # --------------------- checkpoint (de)ser ------------------------
    def _encode_cp(self, cp: Checkpoint) -> Dict[str, Any]:
        return {
            "v": cp["v"],
            "id": cp["id"],
            "ts": cp["ts"],
            "channelValues": {
                k: self._safe_dump_deep(v) for k, v in cp["channel_values"].items()
            },
            "channelVersions": cp["channel_versions"],
            "versionsSeen": cp["versions_seen"],
            "pendingSends": [] # как в BasePostgresSaver, они внутри checkpoint не нужны
        }

    def _decode_cp(self, raw: Dict[str, Any]) -> Checkpoint:
        # Поддерживаем приём pendingSends (если сервер их отдаёт),
        # но сами их не шлём при записи.
        pending_sends: list[Tuple[str, Any]] = []
        for obj in raw.get("pendingSends", []) or []:
            if isinstance(obj, dict) and "channel" in obj:
                channel = obj["channel"]
                value_payload: Any = obj.get("value")
                if value_payload is None and all(k in obj for k in TYPED_KEYS):
                    value_payload = {k: obj[k] for k in TYPED_KEYS}
                pending_sends.append((channel, self._safe_load_deep(value_payload)))
            elif isinstance(obj, (list, tuple)) and len(obj) >= 2:
                channel = obj[0]
                value_payload = obj[1]
                pending_sends.append((channel, self._safe_load_deep(value_payload)))
            else:
                pending_sends.append(obj)
        return Checkpoint(
            v=raw["v"],
            id=raw["id"],
            ts=raw["ts"],
            channel_values={
                k: self._safe_load_deep(v) for k, v in raw["channelValues"].items()
            },
            channel_versions=raw["channelVersions"],
            versions_seen=raw["versionsSeen"],
            pending_sends=pending_sends,
        )

    def _decode_config(self, raw: Dict[str, Any] | None) -> Optional[RunnableConfig]:
        if not raw:
            return None
        return RunnableConfig(
            tags=raw.get("tags"),
            metadata=raw.get("metadata"),
            callbacks=raw.get("callbacks"),
            run_name=raw.get("run_name"),
            max_concurrency=raw.get("max_concurrency"),
            recursion_limit=raw.get("recursion_limit"),
            configurable=self._decode_configurable(raw.get("configurable") or {}),
        )

    def _decode_configurable(self, raw: Dict[str, Any]) -> dict[str, Any]:
        return {
            "thread_id": raw.get("threadId"),
            "thread_ts": raw.get("threadTs"),
            "checkpoint_ns": raw.get("checkpointNs"),
            "checkpoint_id": raw.get("checkpointId")
        }

    # metadata (de)ser
    def _enc_meta(self, md: CheckpointMetadata) -> CheckpointMetadata:
        if not md:
            return {}
        out: CheckpointMetadata = {}
        for k, v in md.items():
            out[k] = self._enc_meta(v) if isinstance(v, dict) else self._safe_dump_deep(v)  # type: ignore[assignment]
        return out

    def _dec_meta(self, md: Any) -> Any:
        if isinstance(md, dict):
            return {k: self._dec_meta(v) for k, v in md.items()}
        return self._safe_load_deep(md)

    # ------------------------ HTTP wrapper ---------------------------
    async def _http(
        self,
        method: str,
        path: str,
        *,
        ok_statuses: Iterable[int] | None = None,
        label_path: str | None = None,
        **kw,
    ) -> httpx.Response:
        if "json" in kw:
            payload = kw.pop("json")
            kw["data"] = orjson.dumps(payload)
            logger.debug("AGW HTTP payload: %s", kw["data"].decode())

        ok_set = set(ok_statuses) if ok_statuses is not None else set()
        metric_path = label_path or path

        attempt = 1
        while True:
            # клиент должен принадлежать текущему loop
            current_loop = asyncio.get_running_loop()
            client = self._client
            if client is None or client.is_closed or self._client_loop is not current_loop:
                if client is not None:
                    try:
                        await client.aclose()
                    except Exception as e:
                        logger.exception("ошибка при закрытии клиента", e)
                client = self._create_client()
                self._client = client
                self._client_loop = current_loop
            try:
                resp = await client.request(method, path, **kw)
            except httpx.RequestError as exc:
                AGW_HTTP_ERROR.labels(method, metric_path).inc()
                logger.warning(
                    "AGW request %s %s failed on attempt %d/%d: %s",
                    method,
                    path,
                    attempt,
                    self.retry_max_attempts,
                    exc,
                )
                if attempt >= self.retry_max_attempts:
                    AGW_HTTP_FINAL_ERROR.labels(method, metric_path).inc()
                    if self._client is not None:
                        try:
                            await self._client.aclose()
                        except Exception as close_exc:  # pragma: no cover
                            logger.debug(
                                "Failed to close AGW httpx.AsyncClient: %s",
                                close_exc,
                            )
                        finally:
                            self._client = None
                            self._client_loop = None
                    raise

                if self._client is not None:
                    try:
                        await self._client.aclose()
                    except Exception as close_exc:  # pragma: no cover
                        logger.debug(
                            "Failed to close AGW httpx.AsyncClient: %s",
                            close_exc,
                        )
                    finally:
                        self._client = None
                        self._client_loop = None
                delay = self._compute_retry_delay(attempt)
                if delay > 0:
                    await asyncio.sleep(delay)
                attempt += 1
                continue

            status = resp.status_code
            if status < 400 or status in ok_set:
                AGW_HTTP_SUCCESS.labels(method, metric_path).inc()
                return resp

            AGW_HTTP_ERROR.labels(method, metric_path).inc()
            if status in (404, 406):
                AGW_HTTP_FINAL_ERROR.labels(method, metric_path).inc()
                return resp

            if attempt >= self.retry_max_attempts:
                AGW_HTTP_FINAL_ERROR.labels(method, metric_path).inc()
                return resp

            try:
                await resp.aclose()
            except Exception as exc:  # pragma: no cover - best effort
                logger.debug("Failed to close AGW httpx.Response before retry: %s", exc)

            if self._client is not None:
                try:
                    await self._client.aclose()
                except Exception as close_exc:  # pragma: no cover
                    logger.debug(
                        "Failed to close AGW httpx.AsyncClient: %s",
                        close_exc,
                    )
                finally:
                    self._client = None
                    self._client_loop = None
            delay = self._compute_retry_delay(attempt)
            if delay > 0:
                await asyncio.sleep(delay)
            attempt += 1

    # -------------------- api -> CheckpointTuple ----------------------
    def _to_tuple(self, node: Dict[str, Any]) -> CheckpointTuple:
        pending = None
        if node.get("pendingWrites"):
            pending = []
            for w in node["pendingWrites"]:
                if isinstance(w, dict):
                    first = w.get("first")
                    second = w.get("second")
                    third = w.get("third")
                    if third is None and isinstance(second, dict) and all(
                        k in second for k in TYPED_KEYS
                    ):
                        third = second
                    pending.append((first, second, self._safe_load_deep(third)))
                elif isinstance(w, (list, tuple)):
                    if len(w) == 3:
                        first, second, third = w
                    elif len(w) == 2:
                        first, second = w
                        third = None
                    else:
                        continue
                    pending.append((first, second, self._safe_load_deep(third)))
        return CheckpointTuple(
            config=self._decode_config(node.get("config")),
            checkpoint=self._decode_cp(node["checkpoint"]),
            metadata=self._dec_meta(node.get("metadata")),
            parent_config=self._decode_config(node.get("parentConfig")),
            pending_writes=pending,
        )

    # =================================================================
    # async-методы BaseCheckpointSaver
    # =================================================================
    async def aget_tuple(self, cfg: RunnableConfig) -> CheckpointTuple | None:
        cid = get_checkpoint_id(cfg)
        api_cfg = self._to_api_config(cfg)
        tid = api_cfg["threadId"]

        if cid:
            path_template = "/checkpoint/{threadId}/{checkpointId}"
            path = f"/checkpoint/{tid}/{cid}"
            params = {"checkpointNs": api_cfg.get("checkpointNs", "")}
        else:
            path_template = "/checkpoint/{threadId}"
            path = f"/checkpoint/{tid}"
            params = None

        resp = await self._http("GET", path, params=params, label_path=path_template)
        logger.debug("AGW aget_tuple response: %s", resp.text)

        if not resp.text:
            return None
        if resp.status_code in (404, 406):
            return None
        resp.raise_for_status()
        return self._to_tuple(resp.json())

    async def alist(
        self,
        cfg: RunnableConfig | None,
        *,
        filter: Dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        payload = {
            "config": self._to_api_config(cfg) if cfg else None,
            "filter": filter,
            "before": self._to_api_config(before) if before else None,
            "limit": limit,
        }
        resp = await self._http(
            "POST",
            "/checkpoint/list",
            json=payload,
            label_path="/checkpoint/list",
        )
        logger.debug("AGW alist response: %s", resp.text)
        resp.raise_for_status()
        for item in resp.json():
            yield self._to_tuple(item)

    async def aput(
        self,
        cfg: RunnableConfig,
        cp: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        payload = {
            "config": self._to_api_config(cfg),
            "checkpoint": self._encode_cp(cp),
            "metadata": self._enc_meta(get_checkpoint_metadata(cfg, metadata)),
            "newVersions": new_versions,
        }
        resp = await self._http("POST", "/checkpoint", json=payload, label_path="/checkpoint")
        logger.debug("AGW aput response: %s", resp.text)
        resp.raise_for_status()
        return resp.json()["config"]

    async def aput_writes(
        self,
        cfg: RunnableConfig,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        enc = [{"first": ch, "second": self._safe_dump_deep(v)} for ch, v in writes]
        payload = {
            "config": self._to_api_config(cfg),
            "writes": enc,
            "taskId": task_id,
            "taskPath": task_path,
        }
        resp = await self._http(
            "POST",
            "/checkpoint/writes",
            json=payload,
            label_path="/checkpoint/writes",
        )
        logger.debug("AGW aput_writes response: %s", resp.text)
        resp.raise_for_status()

    async def adelete_thread(self, thread_id: str) -> None:
        resp = await self._http(
            "DELETE",
            f"/checkpoint/{thread_id}",
            label_path="/checkpoint/{threadId}",
        )
        resp.raise_for_status()

    # =================================================================
    # sync-обёртки
    # =================================================================
    def _run(self, coro):
        # sync-обёртки всегда выполняем в собственном loop в отдельном потоке
        loop = self._ensure_bg_loop()
        fut = asyncio.run_coroutine_threadsafe(coro, loop)
        return fut.result()

    def list(
        self,
        cfg: RunnableConfig | None,
        *,
        filter: Dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        async def _collect():
            out = []
            async for item in self.alist(cfg, filter=filter, before=before, limit=limit):
                out.append(item)
            return out

        for item in self._run(_collect()):
            yield item

    def get_tuple(self, cfg: RunnableConfig) -> CheckpointTuple | None:
        return self._run(self.aget_tuple(cfg))

    def put(
        self,
        cfg: RunnableConfig,
        cp: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        return self._run(self.aput(cfg, cp, metadata, new_versions))

    def put_writes(
        self,
        cfg: RunnableConfig,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        self._run(self.aput_writes(cfg, writes, task_id, task_path))

    def delete_thread(self, thread_id: str) -> None:
        self._run(self.adelete_thread(thread_id))

    def get_next_version(self, current: Optional[str], channel: ChannelProtocol) -> str:
        if current is None:
            current_v = 0
        elif isinstance(current, int):
            current_v = current
        else:
            current_v = int(current.split(".")[0])
        next_v = current_v + 1
        next_h = random()
        return f"{next_v:032}.{next_h:016}"

    # ------------------------------------------------------------------ #
    # Convenience factory                                                #
    # ------------------------------------------------------------------ #
    @classmethod
    @asynccontextmanager
    async def from_base_url(
        cls,
        base_url: str,
        *,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator["AsyncAGWCheckpointSaver"]:
        saver = cls(base_url, api_key=api_key, **kwargs)
        try:
            yield saver
        finally:
            if saver._client is not None:
                try:
                    await saver._client.aclose()
                except Exception as close_exc:  # pragma: no cover - best effort
                    logger.debug("Failed to close AGW httpx.AsyncClient: %s", close_exc)
                finally:
                    saver._client = None
