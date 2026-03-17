# Cloud Integration Analyzer Tool

A Python-based desktop tool to extract data from SAP Cloud Integration (CI) subaccounts via OData APIs, store it in a SQLite database, analyze integration artifacts, and generate HTML migration assessment reports.

## Features

- **API Data Extraction** — Downloads all integration content (packages, IFlows, configurations, security credentials, partner directory) via OData APIs with parallel processing
- **Artifact Analysis** — Extracts and analyzes IFLW XML files: participants, channels, activities, scripts, mappings, timers, content modifiers
- **Environment Variable Scanning** — Detects System (HC_) variable usage across Groovy scripts, JavaScript, and XSLTs
- **Dynamic SQLite Storage** — Infers database schema from JSON structure, stores 24+ table types with tenant isolation
- **Migration Assessment Report** — Comprehensive HTML report for NEO-to-CF migration with per-artifact and per-package readiness indicators, interactive charts, and clickable drill-downs
- **Desktop GUI** — CustomTkinter UI for configuration, report selection, and execution with real-time log streaming
- **Report Selection** — Choose which reports to generate via checkboxes (extensible for future report types)
- **OAuth & Basic Auth** — Supports both authentication methods via factory pattern
- **Cross-Platform Builds** — PyInstaller executables for Windows and macOS via GitHub Actions
- **Post-Run Cleanup** — Optional deletion of downloads folder after report generation to save disk space

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
# REPORT_ONLY = Generate reports from existing database (no API calls, no auth needed)
EXECUTION_MODE=FULL

# Database path for REPORT_ONLY mode
REPORT_DB_PATH=runs/Trial/20260307_164253/ci_analyzer_Trial_20260307_164253.db
```

### Report Selection

```properties
# Select which reports to generate (applies to both FULL and REPORT_ONLY modes)
REPORT_NEO_TO_CF=true
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
CLEANUP_DOWNLOADS=false       # Delete downloads folder after report generation (FULL mode)
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

The GUI provides:
- Configuration form with grouped fields and conditional visibility
- Report Selection checkboxes
- Run & Output tab with real-time log streaming
- Cleanup downloads option (FULL mode only)

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

### Phase 1: Download & Extract

```
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1.0: SETUP                                                    │
│  • Load configuration from .env                                     │
│  • Initialize logging (TRACE/DEBUG/INFO/WARNING/ERROR)              │
│  • Authenticate (OAuth 2.0 or Basic Auth)                           │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1.1: DOWNLOAD OData APIs (JSON)                               │
│                                                                     │
│  ┌──────────────┐  ┌──────────┐  ┌───────────────┐                 │
│  │ Runtime      │  │ Packages │  │ IFlows        │                 │
│  │ Artifacts    │  │          │──▶│ (per package) │                 │
│  └──────────────┘  └────┬─────┘  └───────┬───────┘                 │
│                         │                │                          │
│  ┌──────────────┐  ┌────▼─────┐  ┌───────▼───────┐                 │
│  │ Resources    │  │ Configs  │  │ Script        │                 │
│  │ (per iflow)  │  │(per iflow│  │ Collections   │                 │
│  └──────────────┘  └──────────┘  └───────────────┘                 │
│                                                                     │
│  ┌──────────────┐  ┌──────────┐  ┌───────────────┐                 │
│  │ Message      │  │ Value    │  │ Discover      │                 │
│  │ Mappings     │  │ Mappings │  │ Versions (opt)│                 │
│  └──────────────┘  └──────────┘  └───────────────┘                 │
│                                                                     │
│  ┌──────────────────────────────────────────────────┐               │
│  │ Security APIs                                     │               │
│  │ User Credentials │ OAuth2 Creds │ Secure Params  │               │
│  │ Keystore Entries │ Cert Mappings│ Access Policies │               │
│  └──────────────────────────────────────────────────┘               │
│                                                                     │
│  ┌──────────────────┐                                               │
│  │ Partner Directory │                                              │
│  │ Binary Parameters │                                              │
│  └──────────────────┘                                               │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1.5–1.8: DOWNLOAD & EXTRACT ARTIFACT ZIPs                     │
│                                                                     │
│  1.5  Download ZIPs: READ_ONLY packages, IFlows, Script             │
│       Collections, Message Mappings, Value Mappings                 │
│                                                                     │
│  1.6  Extract READ_ONLY package contents → individual artifacts     │
│                                                                     │
│  1.7  Extract IFlow ZIPs → IFLW files, Groovy scripts,             │
│       JavaScript, XSLT, EDMX/WSDL/XSD schemas, archives            │
│                                                                     │
│  1.8  Extract artifact content → Script Collection scripts,         │
│       Message Mapping files, Value Mapping XML files                │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1.9: IFLW ANALYSIS (XML parsing of extracted IFLW files)      │
│                                                                     │
│  1.9.1  Participants  — Senders, Receivers, Integration Processes   │
│  1.9.2  Channels      — Communication endpoints, adapters, URLs     │
│  1.9.3  Activities    — Process steps, gateways, call activities    │
│  1.9.4  Groovy Scripts— Inline and bundle script references         │
│  1.9.5  Message Maps  — Mapping activity references                 │
│  1.9.6  XSLT Maps    — XSLT transformation references              │
│  1.9.7  Content Mods  — Header/property modifications               │
│  1.9.8  Timers        — Scheduled and event-based timers            │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1.10: ENVIRONMENT VARIABLE SCANNING                           │
│                                                                     │
│  Scans all extracted scripts (Groovy, JS, XSLT) for System (HC_)   │
│  environment variables that need remapping during NEO→CF migration  │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
```

### Phase 2: Database

```
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2.1: CREATE DYNAMIC SCHEMA                                    │
│  Reads all JSON files → infers column types → creates 24+ tables   │
│                                                                     │
│ PHASE 2.2: IMPORT DATA                                              │
│  Bulk imports all OData JSON + IFLW analysis JSON into SQLite      │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
```

### Phase 3: Report Generation

```
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 3: GENERATE REPORTS                                           │
│                                                                     │
│  For each selected report type:                                     │
│    • Query database for all sections                                │
│    • Compute migration readiness (Green/Amber/Red)                  │
│    • Generate HTML with Bootstrap, Chart.js, DataTables             │
│    • Save to runs/{tenant}/{timestamp}/reports/                     │
│                                                                     │
│ CLEANUP (optional):                                                 │
│  Delete downloads/ folder if CLEANUP_DOWNLOADS=true                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Report: NEO to CF Migration Assessment

The main HTML report includes these tabs:

| Tab | Content |
|---|---|
| **Executive Summary** | Clickable KPI cards, migration readiness donut charts, package distribution bar, points to note (version mismatches, drafts, undeployed, expired certs) |
| **Standard Content Analysis** | Design vs Discover version comparison for SAP/partner packages |
| **Package Analysis** | Per-package migration readiness (Green/Amber/Red) with clickable detail modals and readiness distribution bar |
| **Artifact Analysis** | Per-artifact migration readiness based on draft status and System (HC_) variable usage with KPI cards by artifact type |
| **Systems & Adapters** | Connected systems with IFlow drill-down, top 10 adapter type distribution, sender/receiver drill-down |
| **Environment Variables** | System (HC_) variable usage across scripts and XSLTs with file type breakdown |
| **Certificate-User Mappings** | Certificate-to-user mappings (NEO tenants only — shows info message for CF) |
| **Keystore** | Keystore entries with validity status, expiry dates, key types |
| **Download Errors** | Errors encountered during data extraction with error codes and messages |
| **About** | Documentation of each tab, migration readiness indicator logic, and check details |

### Report UI Features

- Gradient header with tenant name, subaccount type, and extraction date
- KPI cards with colored borders, hover lift effects, and click-to-navigate
- Animated counter numbers on page load
- Migration readiness donut charts (Package and Artifact) with percentages
- Clickable readiness indicators (🟢🟡🔴) that open detail modals
- Stacked distribution bars sorted by percentage (descending)
- Sticky tab navigation (stays visible when scrolling)
- Collapsible content sections (click headings to toggle)
- DataTables with search, sort, pagination, and CSV export
- Back-to-top floating button
- Breadcrumb footer with tenant info and generation timestamp

### Migration Readiness Logic

**Per-Artifact** (Artifact Analysis tab):

| Artifact Type | 🟢 Ready | 🟡 Needs Check | 🔴 Action Needed |
|---|---|---|---|
| Integration Flow | Versioned + no HC_ vars | Draft only | Has HC_ variables |
| Script Collection | Versioned + no HC_ vars | Draft only | Has HC_ variables |
| Message Mapping | Versioned | Draft | — |
| Value Mapping | Versioned | Draft | — |

**Per-Package** (Package Analysis tab):

| Package Type | 🟢 Ready | 🟡 Needs Check | 🔴 Action Needed |
|---|---|---|---|
| Standard (Editable & Configure-Only) | Version up-to-date + all artifacts ready | Version or artifacts have issues (not both) | Version outdated AND artifact issues |
| Custom | All artifacts ready + no drafts | Has draft artifacts only | Has HC_ variable artifacts |

## Database Schema

Dynamic schema generated from JSON structure. Key tables:

| Category | Tables |
|---|---|
| **Core** | `package`, `iflow`, `message_mapping`, `script_collection`, `value_mapping` |
| **Configuration** | `configuration`, `resource`, `runtime` |
| **IFLW Analysis** | `iflw_participant`, `iflw_channel`, `iflw_activity`, `iflw_groovy_script`, `iflw_message_mapping`, `iflw_xslt_mapping`, `iflw_content_modifier`, `iflw_timer` |
| **Security** | `security_user_credential`, `security_oauth2_client_credential`, `security_secure_parameter`, `security_keystore_entry`, `security_certificate_user_mapping`, `security_access_policy` |
| **Other** | `partner_directory_binary_parameter`, `environment_variable_check`, `package_discover_version`, `download_error` |

Each record includes `tenant_id` and `captured_at` for multi-tenant isolation.

## Project Structure

```
ci-analyzer-tool/
├── main.py                              # CLI entry point (orchestrates all phases)
├── ui.py                                # Desktop GUI (CustomTkinter)
├── requirements.txt                     # Python dependencies
├── .env.example                         # Configuration template
├── icon.ico                             # Application icon (Windows)
├── icon.png                             # Application icon (source)
├── ci-analyzer-codesign.cer             # Windows code signing certificate
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
│   │   ├── artifact_zip_downloader.py   #   ZIP downloads with retry + error logging
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
│   │   │   └── neo_cf_formatter.py      # HTML report (Bootstrap 5 + Chart.js + DataTables)
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
│       └── downloads/                   # Deleted if CLEANUP_DOWNLOADS=true
│           ├── json-files/              # OData API responses + download errors
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
git tag v1.0.26
git push origin v1.0.26
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
| `No reports selected` | Enable at least one report in the Report Selection configuration |

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11 |
| GUI | CustomTkinter |
| HTTP | requests |
| Database | SQLite3 (built-in) |
| XML Parsing | xml.etree.ElementTree (built-in) |
| HTML Reports | Bootstrap 5, Chart.js 4, DataTables 1.13 |
| Auth | OAuth 2.0 / Basic Auth |
| Build | PyInstaller |
| CI/CD | GitHub Actions |
| Config | python-dotenv |

## References

- [SAP Cloud Integration OData API](https://help.sap.com/docs/SAP_INTEGRATION_SUITE/51ab953548be4459bfe8539ecaeee98d/d1679a80543f46509a7329243b595bdb.html)
- [SAP Integration Suite](https://help.sap.com/docs/SAP_INTEGRATION_SUITE)

## License

MIT License
