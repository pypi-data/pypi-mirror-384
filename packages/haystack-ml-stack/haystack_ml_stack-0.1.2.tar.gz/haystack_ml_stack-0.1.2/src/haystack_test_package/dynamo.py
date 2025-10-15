from typing import Any, Dict, List
import logging

import aiobotocore.session

logger = logging.getLogger(__name__)


async def async_batch_get(
    dynamo_client, table_name: str, keys: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Asynchronous batch_get_item with chunking for requests > 100 keys
    and handling for unprocessed keys.
    """
    all_items: List[Dict[str, Any]] = []
    # DynamoDB's BatchGetItem has a 100-item limit per request.
    CHUNK_SIZE = 100

    # Split the keys into chunks of 100
    for i in range(0, len(keys), CHUNK_SIZE):
        chunk_keys = keys[i : i + CHUNK_SIZE]
        to_fetch = {table_name: {"Keys": chunk_keys}}

        # Inner loop to handle unprocessed keys for the current chunk
        # Max retries of 3
        retries = 3
        while to_fetch and retries > 0:
            retries -= 1
            try:
                resp = await dynamo_client.batch_get_item(RequestItems=to_fetch)

                if "Responses" in resp and table_name in resp["Responses"]:
                    all_items.extend(resp["Responses"][table_name])

                unprocessed = resp.get("UnprocessedKeys", {})
                # If there are unprocessed keys, set them to be fetched in the next iteration
                if unprocessed and unprocessed.get(table_name):
                    logger.warning(
                        "Retrying %d unprocessed keys.",
                        len(unprocessed[table_name]["Keys"]),
                    )
                    to_fetch = unprocessed
                else:
                    # All keys in the chunk were processed, exit the inner loop
                    to_fetch = {}

            except Exception as e:
                logger.error("Error during batch_get_item for a chunk: %s", e)
                # Stop trying to process this chunk on error and move to the next
                to_fetch = {}

    return all_items


def parse_dynamo_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a DynamoDB attribute map (low-level) to Python types."""
    out: Dict[str, Any] = {}
    for k, v in item.items():
        if "N" in v:
            out[k] = float(v["N"])
        elif "S" in v:
            out[k] = v["S"]
        elif "SS" in v:
            out[k] = v["SS"]
        elif "NS" in v:
            out[k] = [float(n) for n in v["NS"]]
        elif "BOOL" in v:
            out[k] = v["BOOL"]
        elif "NULL" in v:
            out[k] = None
        elif "L" in v:
            out[k] = [parse_dynamo_item({"value": i})["value"] for i in v["L"]]
        elif "M" in v:
            out[k] = parse_dynamo_item(v["M"])
    return out


async def set_stream_features(
    *,
    streams: List[Dict[str, Any]],
    stream_features: List[str],
    features_cache,
    features_table: str,
    stream_pk_prefix: str,
    cache_sep: str,
    aio_session: aiobotocore.session.Session | None = None,
) -> None:
    """Fetch missing features for streams from DynamoDB and fill them into streams."""
    if not streams or not stream_features:
        return

    cache_miss: Dict[str, Dict[str, Any]] = {}
    for f in stream_features:
        for s in streams:
            key = f"{s['streamUrl']}{cache_sep}{f}"
            cached = features_cache.get(key)
            if cached is not None:
                s[f] = cached["value"]
            else:
                cache_miss[key] = s

    if not cache_miss:
        return

    logger.info("Cache miss for %d items", len(cache_miss))

    # Prepare keys
    keys = []
    for k in cache_miss.keys():
        stream_url, sk = k.split(cache_sep, 1)
        pk = f"{stream_pk_prefix}{stream_url}"
        keys.append({"pk": {"S": pk}, "sk": {"S": sk}})
    logger.info("Keys prepared for DynamoDB: %s", keys)

    session = aio_session or aiobotocore.session.get_session()
    async with session.create_client("dynamodb") as dynamodb:
        try:
            items = await async_batch_get(dynamodb, features_table, keys)
        except Exception as e:
            logger.error("DynamoDB batch_get failed: %s", e)
            return
        logger.info("DynamoDB returned %d items", len(items))

    for item in items:
        stream_url = item["pk"]["S"].removeprefix(stream_pk_prefix)
        feature_name = item["sk"]["S"]
        cache_key = f"{stream_url}{cache_sep}{feature_name}"
        parsed = parse_dynamo_item(item)
        logger.info("DynamoDB item parsed: %s for %s", parsed, cache_key)

        features_cache[cache_key] = {
            "value": parsed.get("value"),
            "cache_ttl_in_seconds": int(parsed.get("cache_ttl_in_seconds", -1)),
        }
        if cache_key in cache_miss:
            cache_miss[cache_key][feature_name] = parsed.get("value")
