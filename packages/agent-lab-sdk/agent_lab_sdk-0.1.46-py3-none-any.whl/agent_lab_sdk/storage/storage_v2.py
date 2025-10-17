import os
from typing import Optional
import requests
from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    """Ответ от сервиса загрузки файлов"""
    id: Optional[str] = None
    bucket: Optional[str] = None
    key: Optional[str] = None
    storage: Optional[str] = None
    absolute_path: str


def upload_file(filename: str, file_bytes: bytes) -> Optional[FileUploadResponse]:
    """
    Загружает файл в бинарном формате через v2 API и возвращает информацию о загруженном файле.

    Args:
        filename: имя файла
        file_bytes: содержимое файла в виде байтов

    Returns:
        FileUploadResponse с информацией о файле или None в случае ошибки
    """

    ai_agent = os.getenv("AGENT_SERVICE_NAME")
    if not ai_agent:
        raise ValueError("AGENT_SERVICE_NAME environment variable is required")

    gateway_url = os.getenv("STORAGE_PROVIDER_AGW_URL", "http://localhost")
    url = f"{gateway_url}/files/v2/upload"

    headers = {
        "x-agent-id": ai_agent,
        "Content-Type": "application/octet-stream"
    }

    params = {
        "name": filename
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            params=params,
            data=file_bytes
        )
        response.raise_for_status()

        if response.status_code == 200:
            data = response.json()
            return FileUploadResponse(
                id=data.get("id", ""),
                bucket=data.get("bucket", ""),
                key=data.get("key", ""),
                storage=data.get("storage", ""),
                absolute_path=data.get("absolutePath", "")
            )

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке файла через v2 API: {e}")

    return None
