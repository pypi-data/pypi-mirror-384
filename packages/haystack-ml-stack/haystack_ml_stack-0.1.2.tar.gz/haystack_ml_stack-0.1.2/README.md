# Haystack ML Stack

Currently this project contains a FastAPI-based service designed for low-latency scoring of streams data coming from http requests

## 🚀 Features

* **FastAPI Service:** Lightweight and fast web service for ML inference.
    * **Asynchronous I/O:** Utilizes `aiobotocore` for non-blocking S3 and DynamoDB operations.
    * **Model Loading:** Downloads and loads the ML model (using `cloudpickle`) from a configurable S3 path on startup.
    * **Feature Caching:** Implements a thread-safe Time-To-Live (TTL) / Least-Recently-Used (LRU) cache (`cachetools.TLRUCache`) for DynamoDB features, reducing latency and database load.
    * **DynamoDB Integration:** Fetches stream-specific features from DynamoDB to enrich the data before scoring.
    * **Health Check:** Provides a `/health` endpoint to monitor service status and model loading.

## 📦 Installation

This project requires Python 3.11 or later.

1.  **Install package:**
    The dependencies associated are listed in `pyproject.toml`.

    ```bash
    pip install haystack-ml-stack
    ```

## ⚙️ Configuration

The service is configured using environment variables, managed by `pydantic-settings`. You can use a `.env` file for local development.

| Variable Name | Alias | Default | Description |
| :--- | :--- | :--- | :--- |
| `S3_MODEL_PATH` | `S3_MODEL_PATH` | `None` | **Required.** The `s3://bucket/key` URL for the cloudpickled ML model file. |
| `FEATURES_TABLE`| `FEATURES_TABLE`| `"features"` | Name of the DynamoDB table storing stream features. |
| `LOGS_FRACTION` | `LOGS_FRACTION` | `0.01` | Fraction of requests to log detailed stream data for sampling/debugging (0.0 to 1.0). |
| `CACHE_MAXSIZE` | *(none)* | `50000` | Maximum size of the in-memory feature cache. |

**Example env vars**

```env
S3_MODEL_PATH="s3://my-ml-models/stream-scorer/latest.pkl"
FEATURES_TABLE="features"
LOGS_FRACTION=0.05
```

## 🌐 Endpoints
| Method | Path | Description |
| :--- | :--- | :--- |
| **GET** | `/` | Root endpoint, returns a simple running message. |
| **GET** | `/health` | Checks if the service is running and if the ML model has been loaded. |
| **POST** | `/score` | **Main scoring endpoint.** Accepts stream data and returns model predictions. |

## 💻 Technical Details

### Model Structure
The ML model file downloaded from S3 is expected to be a cloudpickle-serialized Python dictionary with the following structure:

``` python

model = {
    "preprocess": <function>,  # Function to transform request data into model input.
    "predict": <function>,     # Function to perform the actual model inference.
    "params": <dict/any>,      # Optional parameters passed to preprocess/predict.
    "stream_features": <list[str]>, # Optional list of feature names to fetch from DynamoDB.
}
```

### Feature Caching (cache.py)
The `ThreadSafeTLRUCache` ensures that feature lookups and updates are thread-safe.
The `_ttu` (time-to-use) policy allows features to specify their own TTL via a `cache_ttl_in_seconds` key in the stored value.

### DynamoDB Feature Fetching (dynamo.py)
The set_stream_features function handles:

- Checking the in-memory cache for required `stream_features`.

- Batch-fetching any missing features from DynamoDB.

- Parsing the low-level DynamoDB items into Python types.

- Populating the cache with the fetched data, respecting the feature's TTL.

- Injecting the fetched feature values back into the streams list in the request payload.