"""
Utility functions for interacting with MinIO/S3 via the Minio Python client.
"""

import logging
from io import BytesIO

import pandas as pd
from minio import Minio
from minio.error import S3Error

try:
    from taskflowbridge.config import settings as app_settings
except ImportError as e:
    raise ImportError(
        "Could not import taskflowbridge.config. Ensure the module is installed and available."
    ) from e


def get_s3_client() -> Minio:
    """Create a S3 client object."""
    try:
        logging.debug("Creating S3 client object.")
        return Minio(
            app_settings.s3.endpoint_url,
            region=app_settings.s3.region,
            access_key=app_settings.s3.access_key,
            secret_key=app_settings.s3.secret_key,
        )
    except Exception as e:
        logging.exception("Unexpected error while creating S3 client object.")
        raise RuntimeError(
            "Unhandled error occurred while creating S3 client object."
        ) from e


def list_s3_files(bucket_name: str, prefix: str, recursive: bool) -> list[str]:
    """Get a list of object names in a S3 bucket with a specific prefix."""
    try:
        minio_client = get_s3_client()
        logging.debug(
            "Listing objects in bucket '%s' with prefix '%s'", bucket_name, prefix
        )
        objects = minio_client.list_objects(
            bucket_name, prefix=prefix, recursive=recursive
        )
        return [obj.object_name for obj in objects if not obj.is_dir]
    except S3Error as e:
        logging.error("S3 error while listing objects.", exc_info=True)
        raise RuntimeError(
            f"S3 error while listing objects in bucket '{bucket_name}' with prefix '{prefix}': {e}"
        ) from e
    except Exception as e:
        logging.exception("Unhandled error while listing objects.")
        raise RuntimeError("Unhandled error while listing S3 objects.") from e


def load_object_from_s3(bucket_name: str, object_path: str) -> bytes:
    """Load an object from an S3 bucket."""
    try:
        minio_client = get_s3_client()
        logging.debug("Loading object '%s' from bucket '%s'", object_path, bucket_name)
        obj = minio_client.get_object(bucket_name, object_path)
        return obj.read()
    except S3Error as e:
        logging.error("S3 error while loading object.", exc_info=True)
        raise RuntimeError(
            f"S3 error while loading object '{object_path}' from bucket '{bucket_name}': {e}"
        ) from e
    except Exception as e:
        logging.exception("Unhandled error while loading object.")
        raise RuntimeError("Unhandled error while loading object from S3.") from e


def put_object_to_s3(bucket_name: str, object_path: str, data: bytes) -> None:
    """Put an object to an S3 bucket."""
    try:
        logging.debug("Putting object '%s' to bucket '%s'", object_path, bucket_name)
        minio_client = get_s3_client()
        minio_client.put_object(
            bucket_name=bucket_name,
            object_name=object_path,
            data=BytesIO(data),
            length=len(data),
            content_type="application/octet-stream",
        )
    except S3Error as e:
        logging.error("S3 error while putting object.", exc_info=True)
        raise RuntimeError(
            f"S3 error while putting object '{object_path}' to bucket '{bucket_name}': {e}"
        ) from e
    except Exception as e:
        logging.exception("Unhandled error while putting object.")
        raise RuntimeError("Unhandled error while putting object to S3.") from e


def load_dataframe_from_s3(
    object_path: str,
    is_csv: bool = True,
    bucket_name: str = "quantfox-airflow-data",
    sep=None,
    sheet_name=None,
) -> pd.DataFrame | None:
    """Load a DataFrame from a file stored in MinIO."""
    try:
        minio_client = get_s3_client()
        logging.debug(
            "Checking if object '%s' exists in bucket '%s'", object_path, bucket_name
        )

        try:
            minio_client.stat_object(bucket_name, object_path)
        except S3Error:
            logging.warning(
                "Object '%s' not found in bucket '%s'", object_path, bucket_name
            )
            return None

        obj = minio_client.get_object(bucket_name, object_path)
        file_content = obj.read()

        if is_csv:
            return pd.read_csv(BytesIO(file_content), sep=sep)
        return pd.read_excel(BytesIO(file_content), sheet_name=sheet_name)

    except S3Error as e:
        logging.error("S3 error while loading DataFrame.", exc_info=True)
        raise RuntimeError(
            f"S3 error while loading object '{object_path}' from bucket '{bucket_name}': {e}"
        ) from e
    except Exception as e:
        logging.exception("Unhandled error while loading DataFrame.")
        raise RuntimeError("Unhandled error while loading DataFrame from S3.") from e


def copy_dataframe_to_s3(
    object_path: str, df: pd.DataFrame, bucket_name: str = "quantfox-airflow-data"
) -> None:
    """Copy a DataFrame to a CSV file stored in S3."""
    try:
        logging.debug(
            "Copying DataFrame to object '%s' in bucket '%s'", object_path, bucket_name
        )
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        minio_client = get_s3_client()
        minio_client.put_object(
            bucket_name=bucket_name,
            object_name=object_path,
            data=csv_buffer,
            length=csv_buffer.getbuffer().nbytes,
            content_type="text/csv",
        )
    except S3Error as e:
        logging.error("S3 error while copying DataFrame.", exc_info=True)
        raise RuntimeError(
            f"S3 error copying DataFrame to object '{object_path}' in bucket '{bucket_name}': {e}"
        ) from e
    except Exception as e:
        logging.exception("Unhandled error while copying DataFrame.")
        raise RuntimeError("Unhandled error while copying DataFrame to S3.") from e


def delete_from_s3(
    object_path: str, bucket_name: str = "quantfox-airflow-data"
) -> None:
    """Delete an object from a S3 bucket."""
    try:
        logging.debug("Deleting object '%s' from bucket '%s'", object_path, bucket_name)
        minio_client = get_s3_client()
        minio_client.remove_object(bucket_name, object_path)
    except S3Error as e:
        logging.error("S3 error while deleting object.", exc_info=True)
        raise RuntimeError(
            f"S3 error while deleting object '{object_path}' from bucket '{bucket_name}': {e}"
        ) from e
    except Exception as e:
        logging.exception("Unhandled error while deleting object.")
        raise RuntimeError("Unhandled error while deleting object from S3.") from e


def delete_folder_from_s3(
    folder_name: str, bucket_name: str = "quantfox-airflow-data"
) -> None:
    """Delete a folder and its contents from a S3 bucket."""
    try:
        logging.debug(
            "Deleting folder '%s' and its contents from bucket '%s'",
            folder_name,
            bucket_name,
        )
        object_names = list_s3_files(bucket_name, prefix=folder_name, recursive=True)
        for obj_name in object_names:
            delete_from_s3(object_path=obj_name, bucket_name=bucket_name)
    except Exception as e:
        logging.exception("Unhandled error while deleting folder and its contents.")
        raise RuntimeError("Unhandled error while deleting folder from S3.") from e
