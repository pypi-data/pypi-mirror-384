"""
This module provides utility functions for the GBIF image downloader application.
It includes functions for hashing images, normalizing and uploading images,
uploading metadata, checking if records exist, validating query parameters and
configuring image settings.
"""

import os
from io import BytesIO
import hashlib
import json
import logging

import io
import time
from typing import BinaryIO

from PIL import Image, ImageFile

from minio import Minio

from anhaltai_commons_minio.io_utils import object_prefix_exists
from anhaltai_commons_minio.helper_utils import normalize_minio_object_name

from anhaltai.gbif_downloader.config import MINIO_CLIENT, BUCKET


def get_image_hash(image_bytes, image_url) -> str | None:
    """
    Computes the SHA-256 hash of an image from its byte content.
    Args:
        image_bytes: BytesIO object containing the image data.
        image_url: URL of the image, used for logging errors.

    Returns:
        The SHA-256 hash of the image, or None if an error occurs.
    """
    try:
        img = Image.open(BytesIO(image_bytes))
        sha256 = hashlib.sha256()
        sha256.update(img.tobytes())
        return sha256.hexdigest()
    except (OSError, ValueError) as e:
        logging.error(
            "[image_url=%s] Error hashing image: %s",
            image_url,
            e,
        )
        return None


def normalize_and_upload_image(
    image_bytes,
    img_path,
):
    """
    Normalizes an image by converting it to RGB format and uploading it to MinIO.
    This function ensures that the image is in a standard format (RGB) and saves it
    as a PNG.
    Args:
        image_bytes: BytesIO object containing the image data.
        img_path: The path where the image will be uploaded in MinIO.
    """

    try:
        with Image.open(BytesIO(image_bytes)) as img:

            if img.mode != "RGB":
                img = img.convert("RGB")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            upload_with_retry(
                object_name=img_path,
                data_bytes=buffer,
                data_length=len(buffer.getvalue()),
                content_type="image/png",
            )

    except (OSError, ValueError) as e:
        logging.error(
            "Error validating/saving normalized image at %s: %s",
            img_path,
            e,
        )


def upload_json(
    record,
    base_dir,
    file_name,
):
    """
    Uploads metadata for a GBIF record to MinIO in JSON format.
    Args:
        record: The GBIF record to be uploaded.
        base_dir: The path in MinIO where the metadata will be stored.
        file_name: The name of the file to which the metadata will be saved (without
        extension).
    """

    metadata_path = os.path.join(base_dir, f"{file_name}.json")

    try:
        json_bytes = json.dumps(record).encode("utf-8")
        byte_stream = io.BytesIO(json_bytes)

        upload_with_retry(
            object_name=metadata_path,
            data_bytes=byte_stream,
            data_length=len(json_bytes),
            content_type="application/json",
        )

    except (OSError, TypeError, ValueError) as e:
        logging.error(
            "Error saving metadata: %s; error: %s",
            metadata_path,
            e,
        )


def does_record_exists(taxonomy_path, file_name):
    """
    Checks if a record exists in MinIO by looking for a specific file.
    Args:
        taxonomy_path: The path in MinIO where the record is expected to be stored.
        file_name: The name of the file to check (without extension).

    Returns:
        True if the record exists, False otherwise.
        Logs an error if there is an issue checking for the record.
    """
    object_path = os.path.join(taxonomy_path, f"{file_name}.json")

    try:
        exists = object_prefix_exists(MINIO_CLIENT, BUCKET, object_path)
        return exists
    except OSError as e:
        logging.error(
            "Error checking if record exists in: %s; error: %s", object_path, e
        )
        return False


def validate_query_params(params):
    """
    Validates the query parameters for GBIF API requests.
    Args:
        params: A dictionary of query parameters to validate.

    Raises:
        ValueError: If an invalid query parameter is found.
    """
    valid_gbif_params = {
        "mediaType",
        "taxonKey",
        "datasetKey",
        "country",
        "hasCoordinate",
        "year",
        "month",
        "basisOfRecord",
        "recordedBy",
        "institutionCode",
        "collectionCode",
        "limit",
        "offset",
    }

    for key in params:
        if key not in valid_gbif_params:
            logging.error("Invalid GBIF query parameter: %s", key)
            raise ValueError(f"Invalid GBIF query parameter: {key}")


def configure_image_settings():
    """
    Configures the image settings to handle large images and truncated images.
    """
    Image.MAX_IMAGE_PIXELS = None
    ImageFile.LOAD_TRUNCATED_IMAGES = True


def upload_with_retry(
    object_name,
    data_bytes,
    data_length,
    content_type,
    retries=3,
    delay=15,
):  # pylint: disable=too-many-arguments, too-many-positional-arguments
    """
    Uploads an object to MinIO with retry logic in case of failure.
    This function attempts to upload the object multiple times if an OSError occurs.
    It uses a semaphore to limit the number of concurrent uploads.
    Args:
        object_name: The name of the object to be uploaded in MinIO.
        data_bytes: BytesIO object containing the data to be uploaded.
        data_length: The length of the data in bytes.
        content_type: The content type of the data being uploaded.
        retries: The number of retry attempts in case of failure.
        delay: The delay in seconds between retry attempts.

    Raises:
        OSError: If the upload fails after all retry attempts.
    """
    for attempt in range(1, retries + 1):
        try:
            upload_object(
                minio_client=MINIO_CLIENT,
                bucket_name=BUCKET,
                object_name=object_name,
                data_bytes=data_bytes,
                data_length=data_length,
                content_type=content_type,
            )
            return

        except OSError as e:

            if attempt == retries:
                logging.error("Upload failed after %s attempts: %s", retries, e)

                raise

            time.sleep(delay)


def upload_object(
    minio_client: Minio,
    bucket_name: str,
    object_name: str,
    data_bytes: BinaryIO,
    data_length: int = -1,
    content_type: str = "application/octet-stream",
    **kwargs,
):  # pylint: disable=too-many-arguments, too-many-positional-arguments
    """Uploads an object to a MinIO bucket.
    Args:
        minio_client: An instance of the Minio client.
        bucket_name: The name of the bucket to upload the object to.
        object_name: The name of the object in the bucket.
        data_bytes: A binary stream containing the data to upload.
        data_length: The length of the data in bytes. If -1, determined automatically.
        content_type: The MIME type of the object being uploaded.
        **kwargs: Additional keyword arguments to pass to the put_object method.
    """

    object_name = normalize_minio_object_name(object_name)

    minio_client.put_object(
        bucket_name=bucket_name,
        object_name=object_name,
        data=data_bytes,
        length=data_length,
        content_type=content_type,
        **kwargs,
    )
