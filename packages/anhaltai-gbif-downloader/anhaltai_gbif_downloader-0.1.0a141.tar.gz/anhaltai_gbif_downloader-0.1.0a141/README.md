# 🌳 GBIF Image Downloader

This project automatically downloads taxon-specific images from the [GBIF API](https://techdocs.gbif.org/en/openapi/),
processes them, and stores both images and metadata in a taxonomically organized structure in a
[MinIO](https://www.min.io/) bucket.

---

## Features

- Loads Latin taxon names from `.csv` or `.xlsx` files
- Resolves `taxonKeys` automatically via the GBIF API
- Downloads associated media (images) from GBIF
- Stores metadata and images in a taxonomic folder structure in MinIO
- Optionally processes only new GBIF occurrences (`crawl_new_entries`)
- Multithreading for parallel processing and uploads
- Saves Logfiles to persistent volume

---

## Project Structure

```plaintext
├── config/
│   └── config.yaml                    # Central configuration (bucket, paths, etc.)
├── data/
│   ├── species_key.csv                # Output: species list with GBIF speciesKeys
│   └── tree_list.xlsx                 # Input: original species list
├── src/
│   └── anhaltai/
│       ├── gbif_downloader/
│       │   ├── crawler/
│       │   │   ├── __init__.py        # Package initialization
│       │   │   └── base_crawler.py    # Base logic for crawling occurrences
│       │   ├── __init__.py            # Package initialization
│       │   ├── config.py              # Loads global configuration
│       │   ├── config_loader.py       # Loads configuration from YAML
│       │   ├── downloader.py          # Download & upload of occurrences and media
│       │   ├── local_log_handler.py   # Log handler that writes logs to MinIO
│       │   ├── main.py                # Entry point, orchestrates all steps
│       │   ├── tree_list_processor.py # Processes taxon lists, resolves taxonKeys
│       │   └── utils.py               # Utility functions (hashing, upload, etc.)
│       └──  __init__.py               # Package initialization
│
├── .dockerignore                      # Files to ignore in Docker build
├── .env                               # MinIO credentials (not in repo)
├── .env-example                       # Example MinIO credentials format
├── .gitattributes                     # Git attributes for line endings
├── .gitignore                         # Files to ignore in git
├── .gitlab-ci.yml                     # GitLab CI/CD configuration
├── Dockerfile                         # Container build
├── LICENSE                            # License information
├── pyproject.toml                     # Python project configuration
├── README.md                          # Project documentation
├── requirements.txt                   # Python dependencies
└── sonar-project.properties           # SonarQube configuration
```

---

## Usage

## Installation

Install dependencies via:

```bash
pip install -r requirements.txt
```

---

### 1. Prepare your input file

Create a `.csv` or `.xlsx` file with at least the following column:

| latin_name      |
|-----------------|
| Quercus robur   |
| Fagus sylvatica |

### 2. Adjust your configuration

Edit the file `config/config.yaml` to set your MinIO connection, output paths, and processing options.  
A typical configuration looks like this:

```yaml
minio:
  bucket: meinewaldki-gbif         # Name of your MinIO bucket
  endpoint: s3.anhalt.ai           # MinIO/S3 endpoint URL
  secure: true                     # Use HTTPS (true/false)
  cert_check: true                 # Check SSL certificates (true/false)

paths:
  output: gbif/                    # Output directory for images and metadata
  tree_list_input_path: data/tree_list.xlsx      # Path to your input taxon list
  processed_tree_list_path: data/species_key.csv # Path for the processed taxonKey list
  log_dir: logs/                   # Directory for log files

query_params:
  mediaType: StillImage            # Only download images
  limit: 100                       # Number of records per API call
  offset: 0                        # Start offset

options:
  already_preprocessed: True         # Set False to process the taxon list again
  crawl_new_entries: False           # Only process new occurrences if True
  max_threads: 300                   # Number of parallel threads for downloads/uploads
  max_pool_size: 50                  # Max connections in Minio-pool
```

#### Query Parameters for GBIF API URL

The parameters used to build the GBIF API request URL are defined in the `query_params` section of your
`config/config.yaml`. These parameters control which records are fetched from the GBIF API.

**Supported parameters:**

- `mediaType` (e.g. `StillImage`): Only download records with images.
- `taxonKey`: The taxon key.
- `datasetKey`: Filter by dataset.
- `country`: Filter by country code (e.g. `DE` for Germany).
- `hasCoordinate`: Only records with coordinates (`true` or `false`).
- `year`, `month`: Filter by year or month of occurrence.
- `basisOfRecord`: Type of record (e.g. `HUMAN_OBSERVATION`).
- `recordedBy`: Filter by collector/observer.
- `institutionCode`, `collectionCode`: Filter by institution or collection.
- `limit`: Number of records per API call (pagination, max. 300).
- `offset`: Start offset for pagination.

**How it works:**

- All parameters in `query_params` are automatically validated at startup.
- Only the above parameters are allowed. Invalid parameters will cause the program to stop with an error.

### 3. Process taxonKey list and resolve taxonKeys

```python
from anhaltai.gbif_downloader.tree_list_processor import TreeListProcessor

processor = TreeListProcessor(input_path="data/tree_list.xlsx",
                              sheet_name="Gehölzarten", taxon="speciesKey")
processor.process_tree_list(output_path="data/species_key.csv")
```

### 4. Download media and metadata from GBIF

Run the main program:

```bash
PYTHONPATH=src python3 src/anhaltai/gbif_extractor/main.py
```

### Note:

- MinIO credentials must be set in `.env` see `.env-example` for the required format\.
- Log files are automatically saved in persistent Volume `mnt/logs/`.
- Parallel processing and uploads are controlled by a configurable thread limit.
- The program will skip old entries if `crawl_new_entries` is set to `True`.
