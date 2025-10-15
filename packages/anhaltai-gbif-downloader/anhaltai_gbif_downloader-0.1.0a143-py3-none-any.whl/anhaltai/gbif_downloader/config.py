"""
Configuration module for the GBIF Downloader project.
This module loads configuration settings from a file and sets up constants
for the application.
"""

from anhaltai_commons_minio.client_utils import get_client
import requests
from requests.adapters import HTTPAdapter
from anhaltai.gbif_downloader.config_loader import load_config
from urllib3 import PoolManager


def create_request_session(
    pool_connections: int = 10, pool_maxsize: int = 10, block: bool = True
):
    """
    Create a requests session with custom connection pooling and retry settings.
    Args:
        pool_connections: Number of connection pools to maintain.
        pool_maxsize: Maximum number of connections in each pool.
        block: Whether to block when the connection pool is exhausted.
    Returns:
        requests.Session: Configured session object.
    """
    session = requests.Session()
    adapter = HTTPAdapter(
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
        pool_block=block,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


CONFIG = load_config()

BUCKET = CONFIG["minio"]["bucket"]
ENDPOINT = CONFIG["minio"]["endpoint"]
SECURE = CONFIG["minio"]["secure"]
CERT_CHECK = CONFIG["minio"]["cert_check"]

OUTPUT_PATH = CONFIG["paths"]["output"]
LOG_DIR = CONFIG["paths"]["log_dir"]
TREE_LIST_INPUT_PATH = CONFIG["paths"]["tree_list_input_path"]
PROCESSED_TREE_LIST_PATH = CONFIG["paths"]["processed_tree_list_path"]

ALREADY_PREPROCESSED = CONFIG["options"]["already_preprocessed"]
CRAWL_NEW_ENTRIES = CONFIG["options"]["crawl_new_entries"]
MAX_THREADS = CONFIG["options"]["max_threads"]
MAX_POOL_SIZE = CONFIG["options"]["max_pool_size"]

QUERY_PARAMS = CONFIG.get("query_params", {})

GBIF_SESSION = create_request_session(pool_maxsize=MAX_POOL_SIZE)

http_client = PoolManager(maxsize=MAX_POOL_SIZE, block=True)

MINIO_CLIENT = get_client(
    secure=SECURE, cert_check=CERT_CHECK, endpoint=ENDPOINT, http_client=http_client
)
