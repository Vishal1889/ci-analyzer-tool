# SAP Cloud Integration Analyzer Tool

A Python-based desktop tool to extract data from SAP Cloud Integration (CI) subaccounts via OData APIs, store it in a SQLite database, analyze integration artifacts, and generate HTML migration assessment reports.

## Features

- **API Data Extraction** — Downloads all integration content (packages, IFlows, configurations, security credentials, partner directory) via OData APIs with parallel processing
- **Artifact Analysis** — Extracts and analyzes IFLW XML files: participants, channels, activities, scripts, mappings, timers, content modifiers
- **Environment Variable Scanning** — Detects System (HC_) variable usage across Groovy scripts, JavaScript, and XSLTs
- **Dynamic SQLite Storage** — Infers database schema from JSON structure, stores 24+ table types with tenant isolation
- **Migration Assessment Report** — Generates a comprehensive HTML report for NEO-to-CF migration with per-artifact and per-package readiness indicators
- **Desktop GUI** — CustomTkinter UI for configuration and execution without command-line usage
- **OAuth & Basic Auth** — Supports both authentication methods via factory pattern
- **Cross-Platform Builds** — PyInstaller executables for Windows and macOS via GitHub Actions

## Installation

### Prerequisites

- Python 3.11+
- SAP Cloud Integration tenant access
- OAuth client credentials (Client ID and Secret)

### Setup

```bash
# Clone the repository
git clone https://github.com/Vishal1889/ci-analyzer-tool.git
cd ci-analyzer-tool

# Create virtual environment
python -m venv venv

# Activate — Windows:
venv\Scripts\activate
# Activate — macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create configuration file
copy .env.example .env    # Windows
cp .env.example .env      # macOS/Linux
```

Edit `.env` with your SAP Cloud Integration credentials (see Configuration below).

## Configuration

The `.env` file controls all settings. Copy `.env.example` and fill in your values:

### Tenant & Authentication

```properties
# Tenant
SAP_TENANT_ID=my-tenant-name
SAP_TENANT_SHORT_NAME=mytenant
SAP_SUBACCOUNT_TYPE=CF              # CF or NEO

# API Endpoint
SAP_API_BASE_URL=https://tenant-id.it-cpi-region.cfapps.region.hana.ondemand.com/api/v1

# Authentication (OAUTH or BASIC — BASIC is NEO-only)
SAP_AUTH_TYPE=OAUTH
SAP_OAUTH_TOKEN_URL=https://tenant.authentication.region.hana.ondemand.com/oauth/token
SAP_CLIENT_ID=your_client_id
SAP_CLIENT_SECRET=your_client_secret
```

### Execution Mode

```properties
# FULL = Download → Analyze → DB → Reports
# REPORT_ONLY = Generate reports from existing database (no API calls)
EXECUTION_MODE=FULL

# Database path for REPORT_ONLY mode
REPORT_DB_PATH=runs/Trial/20260307_164253/ci_analyzer_Trial_20260307_164253.db
```

### Runtime Settings

```properties
LOG_LEVEL=INFO                # TRACE, DEBUG, INFO, WARNING, ERROR
TRACE_API_CALLS=false         # Log full API request/response details
PARALLEL_DOWNLOADS=1          # 1-10 concurrent API workers
API_TIMEOUT=30                # Seconds per API call
API_RETRY_COUNT=3
API_PAGE_SIZE=50
MAX_ARTIFACT_SIZE_MB=50
```

### Discover Integration (Optional)

```properties
# SAP Discover tenant for standard package version checking
DISCOVER_BASE_URL=https://...
DISCOVER_OAUTH_CLIENT_ID=...
DISCOVER_OAUTH_CLIENT_SECRET=...
DISCOVER_OAUTH_TOKEN_URL=...
```

## Usage

### Desktop GUI

```bash
python ui.py
```

The GUI provides a configuration form and a Run & Output tab for execution with real-time log streaming.

### Command Line

```bash
# Full pipeline (download + analyze + report)
python main.py

# Download specific API only
python main.py --api packages

# Download only, skip database and reports
python main.py --save-only

# Enable detailed logging
python main.py --log-level DEBUG
```

### Execution Modes

| Mode | What it does |
|---|---|
| **FULL** | Downloads all APIs → extracts ZIPs → analyzes IFLW files → populates SQLite → generates HTML report |
| **REPORT_ONLY** | Reads from an existing database and generates a fresh HTML report (no API calls, no auth needed) |

## Execution Phases (FULL Mode)

```
Phase 1: DOWNLOAD & EXTRACT
  1.0  Configuration, logging, authentication
  1.1  Download OData APIs (packages, IFlows, configs, security, partner directory)
  1.5  Download artifact ZIPs (IFlows, scripts, mappings)
  1.6  Extract READ_ONLY package contents
  1.7  Extract IFLW content files (groovy, JS, XSLT, schemas)
  1.8  Extract script collection / mapping content
  1.9  IFLW Analysis (participants, channels, activities, scripts,
       message mappings, XSLT mappings, content modifiers, timers)
  1.10 Environment variable scanning (HC_ variables)

Phase 2: DATABASE
  2.1  Create dynamic SQLite schema from JSON files
  2.2  Import all JSON data into database

Phase 3: REPORT GENERATION
  3.1  Generate NEO to CF Migration Assessment (HTML)
```

## Report: NEO to CF Migration Assessment

The main HTML report includes these tabs:

| Tab | Content |
|---|---|
| **Executive Summary** | KPI cards (packages, artifacts, systems), alerts, package distribution |
| **Standard Content Analysis** | Design vs Discover version comparison for SAP/partner packages |
| **Package Analysis** | Per-package migration readiness (Green/Amber/Red) with clickable detail modals |
| **Artifact Analysis** | Per-artifact migration readiness based on draft status and System (HC_) variable usage |
| **Systems & Adapters** | Connected systems, adapter type distribution, IFlow usage drill-down |
| **Environment Variables** | System (HC_) variable usage across scripts and XSLTs |
| **Certificate Mappings** | Certificate-to-user mappings (NEO tenants) |
| **Keystore** | Keystore entries with validity status |

### Migration Readiness Logic

**Per-Artifact** (Artifact Analysis tab):

| Artifact Type | Green | Amber | Red |
|---|---|---|---|
| Integration Flow | Versioned + no HC_ vars | Draft only | Has HC_ variables |
| Script Collection | Versioned + no HC_ vars | Draft only | Has HC_ variables |
| Message Mapping | Versioned | Draft | — |
| Value Mapping | Versioned | Draft | — |

**Per-Package** (Package Analysis tab):

- **Standard packages**: Checks Discover version currency + artifact readiness
- **Custom packages**: Checks artifact readiness + draft status

## Database Schema

Dynamic schema generated from JSON structure. Key tables:

| Category | Tables |
|---|---|
| **Core** | `package`, `iflow`, `message_mapping`, `script_collection`, `value_mapping` |
| **Configuration** | `configuration`, `resource`, `runtime` |
| **IFLW Analysis** | `iflw_participant`, `iflw_channel`, `iflw_activity`, `iflw_groovy_script`, `iflw_message_mapping`, `iflw_xslt_mapping`, `iflw_content_modifier`, `iflw_timer` |
| **Security** | `security_user_credential`, `security_oauth2_client_credential`, `security_secure_parameter`, `security_keystore_entry`, `security_certificate_user_mapping`, `security_access_policy` |
| **Other** | `partner_directory_binary_parameter`, `environment_variable_check`, `package_discover_version` |

Each record includes `tenant_id` and `captured_at` for multi-tenant isolation.

## Project Structure

```
ci-analyzer-tool/
├── main.py                              # CLI entry point (orchestrates all phases)
├── ui.py                                # Desktop GUI (CustomTkinter)
├── requirements.txt                     # Python dependencies
├── .env.example                         # Configuration template
├── CI-Analyzer.spec                     # PyInstaller build spec
├── icon.ico                             # Application icon (Windows)
├── icon.png                             # Application icon (source)
│
├── src/
│   ├── auth/                            # Authentication
│   │   ├── auth_factory.py              #   Factory: creates OAuth or Basic client
│   │   ├── oauth_client.py              #   OAuth 2.0 client credentials flow
│   │   └── basic_auth_client.py         #   Basic auth (NEO only)
│   │
│   ├── downloader/                      # API data downloaders
│   │   ├── base_downloader.py           #   Base class (HTTP, pagination, logging)
│   │   ├── package_downloader.py        #   Packages API
│   │   ├── iflow_downloader.py          #   IFlows API (parallel)
│   │   ├── configuration_downloader.py  #   Configurations API
│   │   ├── resource_downloader.py       #   Resources API
│   │   ├── message_mapping_downloader.py
│   │   ├── value_mapping_downloader.py
│   │   ├── script_collection_downloader.py
│   │   ├── security_downloader.py       #   Security APIs (credentials, certs, policies)
│   │   ├── partner_directory_downloader.py
│   │   ├── discover_version_checker.py  #   SAP Discover version comparison
│   │   ├── artifact_zip_downloader.py   #   ZIP downloads with retry
│   │   ├── iflow_zip_extractor.py       #   IFLW/script/schema extraction
│   │   ├── artifact_content_extractor.py
│   │   └── readonly_package_extractor.py
│   │
│   ├── parsers/                         # JSON response parsers
│   │   ├── package_parser.py
│   │   ├── iflow_parser.py
│   │   ├── configuration_parser.py
│   │   ├── resource_parser.py
│   │   ├── message_mapping_parser.py
│   │   ├── value_mapping_parser.py
│   │   └── script_collection_parser.py
│   │
│   ├── analysers/                       # IFLW content analyzers
│   │   ├── iflw_participant_extractor.py
│   │   ├── iflw_channel_extractor.py
│   │   ├── iflw_activity_extractor.py
│   │   ├── iflw_script_extractor.py
│   │   ├── iflw_message_mapping_extractor.py
│   │   ├── iflw_xslt_mapping_extractor.py
│   │   ├── iflw_content_modifier_extractor.py
│   │   ├── iflw_timer_extractor.py
│   │   ├── iflw_process_activity_resolver.py
│   │   └── environment_variable_scanner.py
│   │
│   ├── database/
│   │   └── db_manager.py                # Dynamic schema generation + bulk import
│   │
│   ├── report_generators/
│   │   ├── base_report.py               # Abstract base class
│   │   ├── formatters/
│   │   │   └── neo_cf_formatter.py      # HTML report (Bootstrap + Chart.js + DataTables)
│   │   └── report_types/
│   │       ├── neo_to_cf_migration.py   # NEO→CF Migration Assessment
│   │       ├── package_version_comparison.py
│   │       ├── package_statistics.py
│   │       └── environment_variables.py
│   │
│   └── utils/
│       ├── config.py                    # .env configuration loader
│       ├── logger.py                    # Multi-level logging (custom TRACE level)
│       └── json_filter.py              # OData JSON filtering
│
├── runs/                                # Runtime output (per tenant/timestamp)
│   └── {tenant_id}/{timestamp}/
│       ├── ci_analyzer_{tenant}_{timestamp}.db
│       ├── ci_analyzer_{tenant}_{timestamp}.log
│       ├── reports/
│       │   └── neo_to_cf_migration_assessment_{tenant}_{timestamp}.html
│       └── downloads/
│           ├── json-files/              # OData API responses
│           ├── iflows/
│           │   ├── iflw-files/          # Extracted IFLW XML files
│           │   ├── groovy-scripts/
│           │   ├── java-scripts/
│           │   ├── xslts/
│           │   └── iflw-json-files/     # IFLW analysis output
│           ├── message-mappings/
│           ├── value-mappings/
│           ├── script-collections/
│           ├── partner-directory/
│           └── read-only-packages/
│
└── .github/workflows/
    └── build.yml                        # GitHub Actions: build Windows + macOS executables
```

## Build & Release

Executables are built automatically via GitHub Actions when a version tag is pushed:

```bash
git tag v1.0.25
git push origin v1.0.25
```

This triggers:
- **Windows**: PyInstaller `--onedir` build + self-signed code signing → `CI-Analyzer-Windows.zip`
- **macOS**: PyInstaller `--onefile` build + ad-hoc signing → `CI-Analyzer-macOS.zip`
- **GitHub Release**: Created automatically with both artifacts

## Troubleshooting

| Error | Solution |
|---|---|
| `Required environment variable ... is not set` | Check `.env` file exists and contains all required variables |
| `Failed to acquire OAuth token` | Verify OAuth token URL, Client ID, and Client Secret |
| `Connection timeout` | Check network connectivity; increase `API_TIMEOUT` in `.env` |
| `Database is locked` | Close other applications using the DB; ensure single instance |

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11 |
| GUI | CustomTkinter |
| HTTP | requests |
| Database | SQLite3 (built-in) |
| XML Parsing | xml.etree.ElementTree (built-in) |
| HTML Reports | Bootstrap 5, Chart.js, DataTables |
| Auth | OAuth 2.0 / Basic Auth |
| Build | PyInstaller |
| CI/CD | GitHub Actions |
| Config | python-dotenv |

## References

- [SAP Cloud Integration OData API](https://help.sap.com/docs/SAP_INTEGRATION_SUITE/51ab953548be4459bfe8539ecaeee98d/d1679a80543f46509a7329243b595bdb.html)
- [SAP Integration Suite](https://help.sap.com/docs/SAP_INTEGRATION_SUITE)

## License

MIT License
