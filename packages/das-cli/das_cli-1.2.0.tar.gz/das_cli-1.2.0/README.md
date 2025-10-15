# DAS Python Client

A Python library and CLI for interacting with the Data Archive System (DAS) API.

## Table of Contents

- Quickstart
- Installation
- CLI Usage
- Python API
- Configuration
- Examples
- Troubleshooting
- Development
- Contributing
- License

## Quickstart

```bash
# Install
pip install das-cli

# Login (prompts for credentials if omitted)
das login --api-url https://your-das-instance/api

# Search entries
das search entries --attribute Name --query 'name(*core*)' --format table

# Get an entry
das entry get --code 7b.b.4c
```

## Installation

### Requirements

- Python 3.13 or higher

### Install from PyPI

```bash
pip install das-cli
```

### Install from Source

```bash
git clone https://git.nioz.nl/ict-projects/das-cli.git
cd das-cli
pip install -e .
```

## CLI Usage

The package installs a `das` executable for interacting with the DAS API.

### Authentication

```bash
das login --api-url https://your-das-instance/api --username your_username --password your_password
```

- Omit `--username`/`--password` to be prompted securely.

### Search

```bash
das search entries --attribute <AttributeName> --query '<SearchQuery>' \
  --max-results 10 --page 1 --sort-by Name --sort-order asc --format table
```

Options:

- `--max-results <n>`: Maximum results per page (default: 10)
- `--page <num>`: Page number (default: 1)
- `--sort-by <field>`: Field to sort by (default: Name)
- `--sort-order <order>`: `asc` or `desc` (default: asc)
- `--format <format>`: `table`, `json`, or `compact` (default: table)
- `--raw`: Print raw API response

Get a specific entry by ID:

```bash
das search entry <ID> --format table
```

Help for query syntax:

```bash
das search help
```

Example queries:

- Name contains pattern: `name(*pattern*)`
- Multiple conditions: `name(*pattern*);code(*ABC*)`
- Date comparison: `Created at(>2023-01-01)`

### Entries

```bash
# Get entry by code
das entry get --code CODE

# Get entry by ID
das entry get --id ID

# Delete an entry
das entry delete CODE

# Create entries from file or data
das entry create --attribute <AttributeName> <file_path>
# Examples:
#   JSON file (can contain a list of entries)
#   das entry create --attribute core c:\data\entries.json
#   CSV file (rows become entries)
#   das entry create --attribute core c:\data\entries.csv
#   Excel file (rows become entries)
#   das entry create --attribute core c:\data\entries.xls
#   Single entry from data string
#   das entry create --attribute core --data { 'Name': 'Entry 1', ... }
#   Multiple entries from data string
#   das entry create --attribute core --data [{ 'Name': 'Entry 1' }, { 'Name': 'Entry 2' }]

# Update entries from file or data
das entry update --attribute <AttributeName> [--code CODE] <file_path>
# Notes:
# - For bulk updates, each entry must include a Code field
# - For single updates via --data, you can pass --code or include Code in data
# Examples:
#   JSON file (each object must include Code)
#   das entry update --attribute core c:\data\entries.json
#   CSV file (must have Code column)
#   das entry update --attribute core c:\data\entries.csv
#   Excel file (must have Code column)
#   das entry update --attribute core c:\data\entries.xls
#   Single entry with explicit code
#   das entry update --attribute core --code ENT001 --data { 'Grant Public Access': Yes }
#   Single entry with Code in data
#   das entry update --attribute core --data { 'Code': 'ENT001', 'Grant Public Access': Yes }
#   Multiple entries from data string (each must include Code)
#   das entry update --attribute core --data [{ 'Code': 'ENT001' }, { 'Code': 'ENT002' }]
```

#### Upload and link a digital object

```bash
# Upload a file as a digital object and link it to an entry
das entry upload-digital-object --entry-code ENT001 --type Dataset --description "CTD raw" c:\data\ctd.zip
```

#### Link or unlink digital objects

```bash
# Link digital objects by their codes to an entry
das entry link-digital-objects --entry-code ENT001 -d DO001 -d DO002

# Unlink digital objects from an entry
das entry link-digital-objects --entry-code ENT001 -d DO003 --unlink
```

#### Change ownership

```bash
# Transfer ownership of one or more entries to a user
das entry chown --user alice --code ENT001 --code ENT002
```

### Hangfire

```bash
das hangfire sync-doi ID
```

### Attributes

```bash
# By ID
das attribute get --id 123

# By name
das attribute get --name "temperature"

# By alias
das attribute get --alias "temp"

# By table name
das attribute get --table-name "measurements"

# Converters
das attribute get-name 123
das attribute get-id "temperature"
```

### Cache

```bash
das cache list
das cache clear "cache-name"
das cache clear-all
```

### Configuration

```bash
# Enable SSL certificate verification (recommended)
das config ssl-verify true

# Disable SSL certificate verification (development/testing only)
das config ssl-verify false

# Show current SSL verification status
das config ssl-status

# Reset all configuration (clears credentials and settings)
das config reset --force
```

### AI

```bash
# Start interactive DAS AI session (prompts for OpenAI API key if needed)
das ai enable

# Clear saved OpenAI key and auth token
das ai clear [--force]

# Alias for `das ai clear`
das ai logout [--force]
```

## Python API

### Basic Usage

```python
from das.app import Das

client = Das("https://your-das-instance/api")

# Authenticate
token = client.authenticate("username", "password")

# Entries
entry = client.entries.get_entry("7b.b.4c")  # by code
entry = client.entries.get_entry(id=123)      # by id
client.entries.delete("7b.b.4c")

# Search
from das.managers.search_manager import SearchManager
search_manager = SearchManager()
results = search_manager.search_entries(
    attribute="Cores",
    query="name(*64*)",
    max_results=10,
    page=1,
    sort_by="Name",
    sort_order="asc",
)

# Downloads
from das.managers.download_manager import DownloadManager
download_manager = DownloadManager()

# Create a download request
request_data = {
    'name': 'My Download Request',
    'ENT001': ['FILE001', 'FILE002'],
    'ENT002': []  # All files from this entry
}
request_id = download_manager.create_download_request(request_data)

# Delete a download request
download_manager.delete_download_request("6b0e68e6-00cd-43a7-9c51-d56c9c091123")

# List your download requests
my_requests = download_manager.get_my_requests()

# Hangfire
client.hangfire.sync_doi("123")

# Attributes
attribute = client.attributes.get_attribute(id=123)
attribute = client.attributes.get_attribute(name="temperature")
attribute = client.attributes.get_attribute(alias="temp")
attribute = client.attributes.get_attribute(table_name="measurements")
name = client.attributes.get_name(123)
attr_id = client.attributes.get_id("temperature")

# Cache
cache_entries = client.cache.get_all()
client.cache.clear_cache("cache-name")
client.cache.clear_all()

# SSL verification
from das.common.config import save_verify_ssl, load_verify_ssl
save_verify_ssl(True)   # enable (recommended)
save_verify_ssl(False)  # disable (dev/testing)
current_setting = load_verify_ssl()
```

## Configuration

### SSL certificate verification

```bash
# Enable (default)
das config ssl-verify true

# Disable (development/testing only)
das config ssl-verify false

# Check status
das config ssl-status
```

## Downloads

```bash
# Create a download request
das download request --entry ENT001 --name "My Download Request"

# Create a request with specific files
das download request --entry ENT001 --file FILE001 --file FILE002

# Create a request with multiple entries
das download request --entry ENT001 --entry ENT002 --name "Multiple Entries"

# Create a request from JSON file
das download request --from-file request.json

# List your download requests
das download my-requests --format table

# Delete a download request
das download delete-request 6b0e68e6-00cd-43a7-9c51-d56c9c091123
```

## Examples

```bash
# List cache and clear a specific cache
das cache list
das cache clear "attributes"

# Dump a single entry as JSON
das search entry 123 --format json

# Paginate through search results
das search entries --attribute Name --query 'name(*core*)' --max-results 50 --page 2

# List your download requests
das download my-requests --format table

# Reset all configuration
das config reset --force
```

## Troubleshooting

- Authentication failed:
  - Ensure `--api-url` points to the correct DAS instance base URL (often ends with `/api`).
  - Try re-running `das login` without passing password to be prompted.
- SSL certificate errors:
  - Use `das config ssl-verify false` temporarily in non-production environments.
  - Consider configuring your corporate CA store instead of disabling verification.
- Proxy/network issues:
  - Respect environment variables `HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY` if required.
- Windows PowerShell quoting:
  - Prefer single quotes for queries, or escape `*` and `;` as needed (e.g., `\*`).
- Unexpected output formatting:
  - Switch format with `--format json` or `--format compact`.

## Dependencies

Runtime and development dependencies are declared in `requirements.txt` and `pyproject.toml`. Install via `pip install das-cli` or `pip install -e .` for development.

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://git.nioz.nl/ict-projects/das-cli.git
cd das-cli

# Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\activate  # On Windows
source venv/bin/activate    # On Unix/macOS

# Install in editable mode
pip install -e .

# (Optional) Install dev/test tooling
pip install -e .[dev]
```

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run a specific test file
python -m pytest tests/specific_test_file.py
```

## Contributing

Contributions are welcome! Please open a Pull Request.

Report bugs or request features via the [DAS CLI issue tracker](https://git.nioz.nl/ict-projects/das-cli/-/issues).

## License

MIT License

## Maintainers

This project is maintained by the Royal Netherlands Institute for Sea Research (NIOZ).
