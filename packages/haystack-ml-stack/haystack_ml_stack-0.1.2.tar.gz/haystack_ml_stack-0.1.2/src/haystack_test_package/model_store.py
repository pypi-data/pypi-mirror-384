import logging
import os
from typing import Any, Dict

import aiobotocore.session
import cloudpickle

logger = logging.getLogger(__name__)


async def download_and_load_model(
    s3_url: str, aio_session: aiobotocore.session.Session | None = None
) -> Dict[str, Any]:
    """
    Downloads cloudpickled model dict from S3 and loads it.
    Expected keys: 'preprocess', 'predict', 'params', optional 'stream_features'.
    """
    if not s3_url or not s3_url.startswith("s3://"):
        raise ValueError("S3_MODEL_PATH must be a valid s3:// URL")

    bucket, key = s3_url.replace("s3://", "").split("/", 1)
    pid = os.getpid()
    local_path = f"/tmp/model_{pid}.pkl"

    session = aio_session or aiobotocore.session.get_session()
    async with session.create_client("s3") as s3:
        logger.info("Downloading model from %s...", s3_url)
        resp = await s3.get_object(Bucket=bucket, Key=key)
        data = await resp["Body"].read()
        with open(local_path, "wb") as f:
            f.write(data)
        logger.info("Model downloaded to %s", local_path)

    with open(local_path, "rb") as f:
        model: Dict[str, Any] = cloudpickle.load(f)
    return model