from minio import Minio
from minio.error import S3Error
from ..core.config import settings
import io
import logging

logger = logging.getLogger(__name__)

class MinioClient:
    def __init__(self):
        # self.client = Minio(
        #     'localhost:9000',
        #     access_key='minioadmin',
        #     secret_key='minioadmin',
        #     secure=False
        # )
        self.client = Minio(
            'localhost:9000',
            access_key='admin',
            secret_key='password',
            secure=False
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise

    def upload_file(self, file_path: str, object_name: str, content_type: str = "application/octet-stream"):
        try:
            self.client.fput_object(
                self.bucket_name,
                object_name,
                file_path,
                content_type=content_type
            )
            return self.get_file_url(object_name)
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            raise

    def upload_bytes(self, data: bytes, object_name: str, content_type: str = "application/octet-stream"):
        try:
            self.client.put_object(
                self.bucket_name,
                object_name,
                io.BytesIO(data),
                len(data),
                content_type=content_type
            )
            return self.get_file_url(object_name)
        except S3Error as e:
            logger.error(f"Error uploading bytes: {e}")
            raise

    def get_file_url(self, object_name: str):
        # For now, return a direct URL assuming public access or internal use
        # In production, you might want presigned URLs
        protocol = "https" if settings.MINIO_SECURE else "http"
        return f"{protocol}://{settings.MINIO_ENDPOINT}:{settings.MINIO_PORT}/{self.bucket_name}/{object_name}"

    def get_file_content(self, object_name: str):
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            return response.read()
        except S3Error as e:
            logger.error(f"Error getting file content: {e}")
            raise
        finally:
            if 'response' in locals():
                response.close()
                
    def download_file(self, object_name: str, file_path: str):
        try:
            self.client.fget_object(self.bucket_name, object_name, file_path)
        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            raise

    def delete_object(self, object_name: str):
        try:
            self.client.remove_object(self.bucket_name, object_name)
        except S3Error as e:
            logger.error(f"Error deleting object: {e}")
            raise

minio_client = MinioClient()
