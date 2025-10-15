import logging
import os
import random
import sys
from http import HTTPStatus
from typing import Any, Dict, List, Optional

import aiobotocore.session
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder

from .cache import make_features_cache
from .dynamo import set_stream_features
from .model_store import download_and_load_model
from .settings import Settings

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] [%(process)d] %(name)s : %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)

logger = logging.getLogger(__name__)


def create_app(
    settings: Optional[Settings] = None,
    *,
    preloaded_model: Optional[Dict[str, Any]] = None,
) -> FastAPI:
    """
    Build a FastAPI app with injectable settings and model.
    If `preloaded_model` is None, the app will load from S3 on startup.
    """
    cfg = settings or Settings()

    app = FastAPI(
        title="ML Stream Scorer",
        description="Scores video streams using a pre-trained ML model and DynamoDB features.",
        version="1.0.0",
    )

    # Mutable state: cache + model
    features_cache = make_features_cache(cfg.cache_maxsize)
    state: Dict[str, Any] = {
        "model": preloaded_model,
        "session": aiobotocore.session.get_session(),
        "model_name": (
            os.path.basename(cfg.s3_model_path) if cfg.s3_model_path else None
        ),
    }

    @app.on_event("startup")
    async def _startup() -> None:
        if state["model"] is not None:
            logger.info("Using preloaded model.")
            return

        if not cfg.s3_model_path:
            logger.critical("S3_MODEL_PATH not set; service will be unhealthy.")
            return

        try:
            state["model"] = await download_and_load_model(
                cfg.s3_model_path, aio_session=state["session"]
            )
            state["stream_features"] = state["model"].get("stream_features", [])
            logger.info("Model loaded on startup.")
        except Exception as e:
            logger.critical("Failed to load model: %s", e)

    @app.get("/health", status_code=HTTPStatus.OK)
    async def health():
        model_ok = state["model"] is not None
        if not model_ok:
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="ML Model not loaded",
            )
        return {
            "status": "ok",
            "model_loaded": True,
            "cache_size": len(features_cache),
            "model_name": state.get("model_name"),
            "stream_features": state.get("stream_features", []),
        }

    @app.post("/score", status_code=HTTPStatus.OK)
    async def score_stream(request: Request, response: Response):
        if state["model"] is None:
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="ML Model not loaded",
            )

        try:
            data = await request.json()
        except Exception:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="Invalid JSON payload"
            )

        user = data.get("user", {})
        streams: List[Dict[str, Any]] = data.get("streams", [])
        playlist = data.get("playlist", {})

        if not streams:
            logger.warning("No streams provided for user %s", user.get("userid", ""))
            return {}

        # Feature fetch (optional based on model)
        model = state["model"]
        stream_features = model.get("stream_features", []) or []
        if stream_features:
            logger.info("Fetching stream features for user %s", user.get("userid", ""))
            await set_stream_features(
                aio_session=state["session"],
                streams=streams,
                stream_features=stream_features,
                features_cache=features_cache,
                features_table=cfg.features_table,
                stream_pk_prefix=cfg.stream_pk_prefix,
                cache_sep=cfg.cache_separator,
            )

        # Sampling logs
        if random.random() < cfg.logs_fraction:
            logger.info("User %s streams: %s", user.get("userid", ""), streams)

        # Synchronous model execution (user code)
        try:
            model_input = model["preprocess"](
                user, streams, playlist, model.get("params")
            )
            model_output = model["predict"](model_input, model.get("params"))
        except Exception as e:
            logger.error("Model prediction failed: %s", e)
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Model prediction failed",
            )

        if model_output:
            return jsonable_encoder(model_output)

        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="No model output generated"
        )

    @app.get("/", status_code=HTTPStatus.OK)
    async def root():
        return {
            "message": "ML Scoring Service is running.",
            "model_name": state.get("model_name"),
        }

    return app
