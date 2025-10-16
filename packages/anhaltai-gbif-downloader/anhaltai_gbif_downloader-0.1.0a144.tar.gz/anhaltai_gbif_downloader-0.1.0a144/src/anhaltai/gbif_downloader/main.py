"""
Main entry point for the GBIF image downloader application.
This script initializes logging, validates query parameters, configures image settings,
and processes a list of tree species to download images from GBIF if necessary.
"""

import logging
import random

import pandas as pd

from anhaltai.gbif_downloader.config import (
    LOG_DIR,
    QUERY_PARAMS,
    ALREADY_PREPROCESSED,
    TREE_LIST_INPUT_PATH,
    PROCESSED_TREE_LIST_PATH,
)

from anhaltai.gbif_downloader.utils import (
    validate_query_params,
    configure_image_settings,
)
from anhaltai.gbif_downloader.crawler.base_crawler import GBIFCrawler
from anhaltai.gbif_downloader.local_log_handler import LocalLogHandler
from anhaltai.gbif_downloader.downloader import GBIFImageDownloader
from anhaltai.gbif_downloader.tree_list_processor import TreeListProcessor

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers.clear()

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

local_handler = LocalLogHandler(base_dir=LOG_DIR)
local_handler.setLevel(logging.WARNING)
local_handler.setFormatter(formatter)
logger.addHandler(local_handler)

logger.info("MinIO-Logging started.")

validate_query_params(QUERY_PARAMS)
configure_image_settings()

if not ALREADY_PREPROCESSED:
    processor = TreeListProcessor(
        input_path=TREE_LIST_INPUT_PATH,
        sheet_name="Gehölzarten",
        taxon="speciesKey",
    )
    processor.process_tree_list(PROCESSED_TREE_LIST_PATH)

try:
    df = pd.read_csv(PROCESSED_TREE_LIST_PATH)
except Exception as e:
    logger.error("Error reading CSV file %s: %s", PROCESSED_TREE_LIST_PATH, e)
    raise SystemExit(f"Aborted due to CSV read error: {e}") from e

downloader = GBIFImageDownloader()

species_keys = df["species_key"].dropna().unique().tolist()
# Shuffle to speed up the entire download process so that species_keys at the beginning
# which are almost completely downloaded, do not have to be processed first.
random.shuffle(species_keys)

for species_key in species_keys:

    QUERY_PARAMS["taxonKey"] = int(species_key)

    try:
        crawler = GBIFCrawler(downloader=downloader, query_params=QUERY_PARAMS)
        crawler.crawl()

    except (ValueError, KeyError) as e:
        logger.error("Error processing taxon key %s: %s", int(species_key), e)
        continue

logger.info("MinIO-Logging finished successfully.")
