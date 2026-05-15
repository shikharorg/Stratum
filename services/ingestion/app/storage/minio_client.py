from io import BytesIO
from urllib.parse import urlparse

import structlog
from miniopy_async import Minio

from app.core.config import settings

logger = structlog.get_logger()


class MinIOClient:
    def __init__(self) -> None:
        parsed = urlparse(settings.MINIO_URL)
        self._client = Minio(
            parsed.netloc,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=parsed.scheme == "https",
        )
        self._bucket = settings.MINIO_BUCKET

    async def ensure_bucket(self) -> None:
        exists = await self._client.bucket_exists(self._bucket)
        if not exists:
            await self._client.make_bucket(self._bucket)
            logger.info("minio.bucket_created", bucket=self._bucket)

    async def upload_file(self, object_key: str, data: bytes, content_type: str) -> str:
        await self._client.put_object(
            self._bucket,
            object_key,
            BytesIO(data),
            len(data),
            content_type=content_type,
        )
        logger.info("minio.file_uploaded", bucket=self._bucket, key=object_key, size=len(data))
        return object_key

    async def download_file(self, object_key: str) -> bytes:
        response = await self._client.get_object(self._bucket, object_key)
        try:
            return await response.read()
        finally:
            await response.release()

    async def delete_file(self, object_key: str) -> None:
        await self._client.remove_object(self._bucket, object_key)
        logger.info("minio.file_deleted", bucket=self._bucket, key=object_key)
