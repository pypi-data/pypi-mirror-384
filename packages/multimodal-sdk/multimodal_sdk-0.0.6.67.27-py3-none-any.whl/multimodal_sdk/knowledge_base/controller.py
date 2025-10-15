import aiohttp
import os
import logging
from multimodal_sdk.common.refresh import token_refresh_handler
from multimodal_sdk.common.http_status_handler import HTTPStatusHandler
from multimodal_sdk.common.decorators import log_and_authorize
from multimodal_sdk.common.retry_decorator import retry_on_client_error
from multimodal_sdk.knowledge_base.poll_task_status import PollTaskStatusNamespace
from multimodal_sdk.common.rate_limiter import rate_limiter
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Union

import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@retry_on_client_error()
@token_refresh_handler
@log_and_authorize
@HTTPStatusHandler(201)
async def create_collection_func(
    kb_resource_id,
    collection_name,
    ingestion_strategy,
    distance_method=None,
    main_lang=None,
    chunk_strategy=None,
    embedding_strategy=None,
    **kwargs
):
    payload = {
        "name": collection_name,
        "ingestion_strategy": {
            "for_types": ingestion_strategy
        },
        "distance_method": distance_method if distance_method else "cosine",
        "main_lang": main_lang if main_lang else "ja",
        "chunk_strategy": chunk_strategy if chunk_strategy else {"active": True, "max_size": "auto"}
    }

    if embedding_strategy is not None:
        payload["embedding_strategy"] = embedding_strategy
    
    logger.info("KnowledgeBase: create_collection payload: %s", payload)
    
    url = f"{kwargs['base_url']}/knowledge-bases/{kb_resource_id}/collections"

    async with aiohttp.ClientSession() as session:
        async with rate_limiter:
            return await session.post(url, json=payload, headers=kwargs['headers'])

@retry_on_client_error()
@token_refresh_handler
@log_and_authorize
@HTTPStatusHandler(204)
async def delete_collection_func(
    kb_resource_id,
    collection_name,
    **kwargs
):
    url = f"{kwargs['base_url']}/knowledge-bases/{kb_resource_id}/collections"
    payload = {
        "name": collection_name
    }

    async with aiohttp.ClientSession() as session:
        async with rate_limiter:
            return await session.delete(url, json=payload, headers=kwargs['headers'])

@retry_on_client_error()
@token_refresh_handler
@log_and_authorize
@HTTPStatusHandler(200)
async def get_collection_func(
    kb_resource_id,
    **kwargs
):
    url = f"{kwargs['base_url']}/knowledge-bases/{kb_resource_id}/collections"

    async with aiohttp.ClientSession() as session:
        async with rate_limiter:
            return await session.get(url, headers=kwargs['headers'])

@retry_on_client_error()
@token_refresh_handler
@log_and_authorize
@HTTPStatusHandler(201)
async def ingest_data_func(
    kb_resource_id,
    tenant_resource_id,
    namespace,
    batch,
    **kwargs
):
    url = f"{kwargs['base_url']}/stores/{tenant_resource_id}/knowledge-bases/{kb_resource_id}"
    logger.info(f"Endpoint URL: {url}")

    form_data = aiohttp.FormData()
    form_data.add_field('namespace', namespace)
    files_to_close = []

    timeout = aiohttp.ClientTimeout(total=600) # 10 minutes

    try:
        for data in batch:
            logger.info(f"Data: {data}")
            # namespace = data.get("namespace")
            # category = data.get("category")
            text = data.get("text")
            file = data.get("data")
            id = data.get("id")
            author = data.get("author", None)
            # Creation date of the data in ISO8601 format.
            created_at = data.get("created_at", None)
            category = data.get("category", [])
            custom_metadata = data.get("custom_metadata", "{}")

            if not author or not created_at:
                raise ValueError("Author and created_at are required fields.")
            
            # Japan TimeZone
            iso_created_at = datetime.fromtimestamp(float(data.get("created_at", 0)), timezone.utc).astimezone(timezone(timedelta(hours=9))).isoformat() if data.get("created_at") else None

            form_data.add_field('record_id', id)
            form_data.add_field('local_str', "ja_JP")
            form_data.add_field('authors', author)
            form_data.add_field('created_at', iso_created_at)
            form_data.add_field('tags', category)
            form_data.add_field('metadata', custom_metadata)

            if text is not None:
                form_data.add_field('text', text)
            
            logger.info("Form data created successfully, till text!")
            
            try:
                if file and os.path.isfile(file):
                    file_path = file  # Keep the original file path
                    file = open(file, 'rb')
                    form_data.add_field('data', file, filename=os.path.basename(file_path))  # Use file_path here
                    files_to_close.append(file)
                elif file:
                    error_message = f"File not found or not a valid file: {file}"
                    logger.error(error_message)
                    raise ValueError(error_message)
            except Exception as e:
                logger.error(f"Error occurred while adding file to form data: {e}")
                raise e

        logger.info("Form data created successfully")

        # Iterate over form data and log
        for field in form_data._fields:
            name = field[0].get("name")   # extract actual key
            value = field[1]
            logger.info(f"Form data field: {name} = {value}")

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with rate_limiter:
                return await session.post(url, data=form_data, headers=kwargs['headers'], ssl=ssl_context)
    finally:
        for file in files_to_close:
            file.close()
            logger.info(f"Closed file: {file.name}")

@retry_on_client_error()
@token_refresh_handler
@log_and_authorize
@HTTPStatusHandler([200, 202])
async def retrieve_data_func(
    kb_resource_id,
    tenant_resource_id,
    threshold=0.7,
    limit=5,
    timeout=20,
    sync=False,
    history=[],
    inject="",
    namespace=[],
    thread_id="",
    create_thread=False,
    **kwargs
):
    debug_query = kwargs.get("debug_query", [])
    if not isinstance(debug_query, list):
        raise ValueError("debug_query must be a list of (key, value) tuples.")

    # Convert to dict and strip keys and values
    query_dict = {k.strip(): v.strip() for k, v in debug_query if isinstance(k, str) and isinstance(v, str)}

    query = query_dict.get("query")
    if not query or not query.strip():
        raise ValueError("Query is required and cannot be empty.")

    # --- Build query params as list-of-tuples so namespace can repeat ---
    # Start from existing query_dict content
    params_pairs = list(query_dict.items())

    # Normalize namespace into a list (avoid iterating over a string)
    if isinstance(namespace, str):
        namespaces_list = [namespace] if namespace.strip() else []
    else:
        namespaces_list = [ns for ns in namespace if isinstance(ns, str) and ns.strip()]

    # Add repeated namespace keys
    for ns in namespaces_list:
        params_pairs.append(("namespace", ns))

    # Optional flags
    if create_thread:
        params_pairs.append(("create_thread", str(bool(create_thread)).lower()))
    if thread_id:
        params_pairs.append(("thread_id", thread_id))

    body = {}
    if history:
        body['msg_history'] = history

    url = f"{kwargs['base_url']}/stores/{tenant_resource_id}/knowledge-bases/{kb_resource_id}/ask"
    logger.info(f"Endpoint URL: {url}")

    # Logging (list-of-tuples)
    logger.info("Query parameters:")
    for key, value in params_pairs:
        logger.info(f"{key}: {value}")

    if body:
        logger.info(f"Request body: {body}")

    async with aiohttp.ClientSession() as session:
        async with rate_limiter:
            # Pass list-of-tuples so aiohttp emits repeated keys
            res = await session.post(url, headers=kwargs['headers'], params=params_pairs, json=body, ssl=ssl_context)
            if res.status != 401:
                result = await PollTaskStatusNamespace.poll_task_status_handler(
                    res,
                    status_url=f"https://192.168.20.20/api/v1/tasks/status",
                    task_id_key='task_token',
                    **kwargs
                )
                return result
            return res

@retry_on_client_error()
@token_refresh_handler
@log_and_authorize
@HTTPStatusHandler([200, 202])
async def retrieve_data_func_beta(
    kb_resource_id,
    query,
    namespace=[],
    inject="",
    thread_id="",
    create_thread=False,
    history=[],
    **kwargs
):
    if not query or not query.strip():
        raise ValueError("Query is required and cannot be empty.")

    params = [("query", query), ("inject", inject), ("version", "beta")]
    params += [("namespace", ns) for ns in namespace if ns]

    body = {}
    # body["query"] = query
    if history:
        body['msg_history'] = history

    if create_thread:
        params['create_thread'] = create_thread
    if thread_id:
        params['thread_id'] = thread_id

    url = f"{kwargs['base_url']}/knowledge-bases/{kb_resource_id}/rag"
    logger.info(f"Endpoint URL: {url}")

    logger.info("Query parameters:")
    for key, value in params.items():
        logger.info(f"{key}: {value}")
    
    if body:
        logger.info(f"Request body: {body}")

    # async with aiohttp.ClientSession() as session:
    #     res = await session.post(url, headers=kwargs['headers'], params=params)
    #     return res
    
    async with aiohttp.ClientSession() as session:
        async with rate_limiter:
            res = await session.post(url, headers=kwargs['headers'], params=params)
            if res.status != 401:
                result = await PollTaskStatusNamespace.poll_task_status_handler(
                    res,
                    status_url=f"http://192.168.1.27:5002/api/v1/tasks/status",
                    task_id_key='task_token',
                    **kwargs
                )
                return result
            return res

@retry_on_client_error()
@token_refresh_handler
@log_and_authorize
@HTTPStatusHandler([200, 202])
async def search_data_func(
    tenant_resource_id,
    kb_resource_id,
    namespace,
    query,
    includes=[],
    limit=50,
    offset=0,
    tags=[],
    authors=[],
    creation_from=None,
    creation_to=None,
    **kwargs
):
    if not query or not query.strip():
        raise ValueError("Query is required and cannot be empty.")

    # params = {
    #     "query": query,
    #     "threshold": 0.7,
    #     "limit": 5,
    #     "includes": "distances",
    #     "sync": "true",
    # }

    params=[]
    params.extend([('namespace', ns) for ns in namespace if ns])
    params.append(('query', query))
    params.append(('limit', limit))
    params.append(('offset', offset))
    if creation_from:
        params.append(('creation_from', creation_from))
    if creation_to:
        params.append(('creation_to', creation_to))
    params.extend([('include', include) for include in includes])
    params.extend([('tag', tag) for tag in tags])
    params.extend([('author', author) for author in authors])

    url = f"{kwargs['base_url']}/stores/{tenant_resource_id}/knowledge-bases/{kb_resource_id}/search"
    logger.info(f"Endpoint URL: {url}")

    for param in params:
        logger.info(f"Query parameter: {param}")

    async with aiohttp.ClientSession() as session:
        async with rate_limiter:
            res = await session.get(url, headers=kwargs['headers'], params=params, ssl=ssl_context)
            return res

@retry_on_client_error()
@token_refresh_handler
@log_and_authorize
@HTTPStatusHandler(204)
async def delete_item_func(
    tenant_id,
    kb_resource_id,
    record_ids=[],
    namespace=None,
    **kwargs
):
    if not record_ids:
        raise ValueError("Record IDs are required and cannot be empty.")
    
    url = f"{kwargs['base_url']}/stores/{tenant_id}/knowledge-bases/{kb_resource_id}"
    logger.info(f"Endpoint URL: {url}")
    params = [("record_id", rec_id) for rec_id in record_ids]
    params.append(('namespace', namespace))

    async with aiohttp.ClientSession() as session:
        async with rate_limiter:
            return await session.delete(url, headers=kwargs['headers'], params=params, ssl=ssl_context)

@retry_on_client_error()
@token_refresh_handler
@log_and_authorize
@HTTPStatusHandler(200)
async def get_ingested_chunks_func(
    kb_resource_id,
    record_id,
    **kwargs
):
    updated_record_id = f"{record_id}"
    # if ingestion_type == "pdf":
    #     if get_chunk_type is None:
    #         updated_record_id = f"{record_id}_script"
    #     else:
    #         updated_record_id = f"{record_id}_summary"
    params = {
        "record_id": updated_record_id,
        "includes": "documents",
        "limit": 5
    }
    url = f"{kwargs['base_url']}/knowledge-bases/{kb_resource_id}/get"

    logger.info(f"Params: {params}")

    # async with aiohttp.ClientSession() as session:
    #     async with rate_limiter:
    #         return await session.get(url, headers=kwargs['headers'], params=params)
    
    async with aiohttp.ClientSession() as session:
        async with rate_limiter:
            res = await session.get(url, headers=kwargs['headers'], params=params)
            if res.status != 401:
                result = await PollTaskStatusNamespace.poll_task_status_handler(
                    res,
                    status_url=f"http://192.168.1.27:5002/api/v1/tasks/status",
                    task_id_key='task_token',
                    **kwargs
                )
                return result
            return res

@retry_on_client_error()
@token_refresh_handler
@log_and_authorize
@HTTPStatusHandler([200, 202])
async def get_kb_records_func(
    tenant_id,
    kb_resource_id,
    record_ids=[],
    namespace=[],
    includes=[],
    status=[],
    limit=50,
    tags=[],
    authors=[],
    offset=0,
    creation_from=None,
    creation_to=None,
    text_search=None,
    text_search_mode=None,
    **kwargs
):
    url = f"{kwargs['base_url']}/stores/{tenant_id}/knowledge-bases/{kb_resource_id}"
    
    # Correctly format the query parameters with multiple `ids[]`
    params = [('record_id', record_id) for record_id in record_ids]
    params.extend([('namespace', ns) for ns in namespace])
    params.extend([('include', include) for include in includes])
    params.extend([('status', stat) for stat in status])
    params.append(('limit', limit))
    params.extend([('tag', tag) for tag in tags])
    params.extend([('author', author) for author in authors])
    params.append(('offset', offset))
    if creation_from:
        params.append(('creation_from', creation_from))
    if creation_to:
        params.append(('creation_to', creation_to))
    if text_search:
        params.append(('text', text_search))
    if text_search_mode:
        params.append(('mode_fts', text_search_mode))

    for param in params:
        logger.info(f"Query parameter: {param}")


    # async with aiohttp.ClientSession() as session:
    #     async with rate_limiter:
    #         res = await session.get(url, headers=kwargs['headers'], params=params, ssl=ssl_context)
    #         if res.status != 401:
    #             result = await PollTaskStatusNamespace.poll_task_status_handler(
    #                 res,
    #                 status_url="https://192.168.20.20/api/v1/tasks/status",
    #                 task_id_key='task_token',
    #                 **kwargs
    #             )
    #             return result
    #         return res

    async with aiohttp.ClientSession() as session:
        async with rate_limiter:
            return await session.get(url, headers=kwargs['headers'], params=params, ssl=ssl_context)


@retry_on_client_error()
@token_refresh_handler
@log_and_authorize
@HTTPStatusHandler(200)
async def get_namespace_metadata_func(
    tenant_resource_id,
    kb_resource_id,
    namespace,
    **kwargs
):
    url = f"{kwargs['base_url']}/stores/{tenant_resource_id}/knowledge-bases/{kb_resource_id}/namespaces/{namespace}"

    # Params: include=authors&include=tags
    params = [
        ("include", "authors"),
        ("include", "tags"),
    ]

    logger.info(f"Params: {params}")
    logger.info(f"URL: {url}")

    async with aiohttp.ClientSession() as session:
        async with rate_limiter:
            return await session.get(url, headers=kwargs['headers'], params=params, ssl=ssl_context)

@retry_on_client_error()
@token_refresh_handler
@log_and_authorize
@HTTPStatusHandler(200)
async def update_ingested_record_func(
    tenant_resource_id,
    kb_resource_id,
    namespace,
    record_id=None,
    author=None,
    tag=None,
    tag_mode=None,
    **kwargs
):
    url = f"{kwargs['base_url']}/stores/{tenant_resource_id}/knowledge-bases/{kb_resource_id}"

    # Build multipart/form-data (only add keys that have a value)
    form = aiohttp.FormData()
    if namespace is not None:
        form.add_field("namespace", str(namespace))
    if record_id is not None:
        form.add_field("record_id", str(record_id))
    if tag is not None:
        form.add_field("tag", str(tag))
    if tag_mode is not None:  # e.g. "discard" | "replace" | "add"
        form.add_field("tag_mode", str(tag_mode))
    if author is not None:
        form.add_field("author", str(author))

    async with aiohttp.ClientSession() as session:
        async with rate_limiter:
            return await session.patch(url, data=form, headers=kwargs['headers'], ssl=ssl_context)


def _as_list(x: Optional[Union[str, List[str]]]) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [v for v in x if v is not None and f"{v}".strip() != ""]
    s = f"{x}".strip()
    return [s] if s else []

@retry_on_client_error()
@token_refresh_handler
@log_and_authorize
@HTTPStatusHandler([200, 202])
async def fetch_kb_records_func(
    tenant_id: str,
    kb_resource_id: str,
    namespace: Optional[Union[str, List[str]]] = None,
    record_ids: Optional[List[str]] = None,
    includes: Optional[List[str]] = None,   # used as "select"
    status: Optional[List[str]] = None,     # ["draft","published"] etc.
    limit: int = 50,
    tags: Optional[List[str]] = None,
    authors: Optional[List[str]] = None,
    offset: int = 0,
    creation_from: Optional[str] = None,    # ISO 8601, e.g. "2025-04-10T00:00:00+09:00"
    creation_to: Optional[str] = None,      # ISO 8601
    sort_by: str = "creation_date",
    order: str = "desc",
    **kwargs
):
    """
    Build request JSON like your working Postman example and POST it.
    - select := includes (pass-through)
    - filters := $and of provided optional conditions
    - creation_dates supports $gte/$lt depending on creation_from/creation_to
    """
    url = f"{kwargs['base_url']}/stores/{tenant_id}/knowledge-bases/{kb_resource_id}/get"

    # Normalize inputs
    ns_list      = _as_list(namespace)
    authors_list = _as_list(authors)
    tags_list    = _as_list(tags)
    status_list  = _as_list(status)
    includes     = includes or []  # if None, send empty (API can decide defaults)
    record_ids   = record_ids or []

    # Build $and conditions
    and_filters: List[dict] = []

    if authors_list:
        and_filters.append({"authors": {"$in": authors_list}})

    if tags_list:
        # If you want exactly "one of these tags", use $in
        and_filters.append({"tags": {"$in": tags_list}})

    if status_list:
        # Your working JSON uses "statuses" (plural) as the field name
        and_filters.append({"statuses": {"$in": status_list}})

    # creation_dates range (match your working payload's field name)
    if creation_from or creation_to:
        range_obj = {}
        if creation_from:
            range_obj["$gte"] = creation_from
        if creation_to:
            range_obj["$lt"] = creation_to
        and_filters.append({"creation_dates": range_obj})

    if record_ids:
        and_filters.append({"record_id": {"$in": record_ids}})

    payload = {
        "namespace": ns_list or [],           # API expects an array
        "select": includes,                   # direct pass-through
        "filters": {"$and": and_filters} if and_filters else {},  # empty {} if no filters
        "limit": limit,
        "offset": offset,
        "sort_by": sort_by,
        "order": order,
    }

    # Use POST with JSON body (your Postman example is a JSON payload).
    async with aiohttp.ClientSession() as session:
        async with rate_limiter:
            return await session.post(
                url,
                headers=kwargs["headers"],
                json=payload,
                ssl=ssl_context
            )

@retry_on_client_error()
@token_refresh_handler
@log_and_authorize
@HTTPStatusHandler([200, 201, 202])
async def add_namespace_keys(
    tenant_id: str,
    kb_resource_id: str,
    namespace: str,
    ns_keys: List[str],
    ns_keys_value_types: List[str],
    **kwargs
):
    if not namespace or not namespace.strip():
        raise ValueError("Namespace is required and cannot be empty.")
    if not ns_keys:
        raise ValueError("ns_keys is required and cannot be empty.")
    if not ns_keys_value_types:
        raise ValueError("ns_keys_value_types is required and cannot be empty.")
    if len(ns_keys) != len(ns_keys_value_types):
        raise ValueError("ns_keys and ns_keys_value_types must have the same length.")

    url = f"{kwargs['base_url']}/stores/{tenant_id}/knowledge-bases/{kb_resource_id}/namespaces/{namespace}/schema"

    form_data = []
    for nt, vt in zip(ns_keys, ns_keys_value_types):
        form_data.append(("key", nt))
        form_data.append(("type_", vt))

    logger.info(f"Endpoint URL: {url}")
    logger.info(f"Form Data: {form_data}")

    async with aiohttp.ClientSession() as session:
        async with rate_limiter:
            return await session.post(
                url,
                headers=kwargs['headers'],
                data=form_data,
                ssl=ssl_context
            )

@retry_on_client_error()
@token_refresh_handler
@log_and_authorize
@HTTPStatusHandler([200, 201])
async def create_namespace_func(
    tenant_id: str,
    kb_resource_id: str,
    namespace: str,
    **kwargs
):
    if not namespace or not namespace.strip():
        raise ValueError("Namespace is required and cannot be empty.")

    url = f"{kwargs['base_url']}/stores/{tenant_id}/knowledge-bases/{kb_resource_id}/namespaces/{namespace}"
    logger.info(f"Endpoint URL: {url}")

    async with aiohttp.ClientSession() as session:
        async with rate_limiter:
            return await session.post(
                url,
                headers=kwargs['headers'],
                ssl=ssl_context
            )

@retry_on_client_error()
@token_refresh_handler
@log_and_authorize
@HTTPStatusHandler(200)
async def get_all_namespaces_func(
    tenant_id: str,
    kb_resource_id: str,
    **kwargs
):
    url = f"{kwargs['base_url']}/stores/{tenant_id}/knowledge-bases/{kb_resource_id}/namespaces"
    logger.info(f"Endpoint URL: {url}")

    async with aiohttp.ClientSession() as session:
        async with rate_limiter:
            return await session.get(
                url,
                headers=kwargs['headers'],
                ssl=ssl_context
            )

@retry_on_client_error()
@token_refresh_handler
@log_and_authorize
@HTTPStatusHandler(200)
async def update_namespace_text_mode_func(
    tenant_id: str,
    kb_resource_id: str,
    namespace: str,
    text_mode: str,
    **kwargs
):
    if not namespace or not namespace.strip():
        raise ValueError("Namespace is required and cannot be empty.")
    
    # Add key:mode_text, value:fulltext as params to the URL (default)
    params = [("mode_text", "fulltext")]
    url = f"{kwargs['base_url']}/stores/{tenant_id}/knowledge-bases/{kb_resource_id}/namespaces/{namespace}"
    logger.info(f"Endpoint URL: {url}")

    async with aiohttp.ClientSession() as session:
        async with rate_limiter:
            return await session.patch(
                url,
                headers=kwargs['headers'],
                params=params,
                ssl=ssl_context
            )