# SAP Cloud Integration Analyzer - Project Structure

## 📁 Directory Organization

```
ci-analyzer-tool/
├── main.py                          # Main entry point
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment configuration template
├── .env                            # Active environment configuration (gitignored)
├── .gitignore                      # Git ignore patterns
├── README.md                       # Project documentation
├── SETUP_GUIDE.md                  # Installation and setup guide
├── PROJECT_STRUCTURE.md            # This file
│
├── src/                            # Source code
│   ├── __init__.py
│   │
│   ├── auth/                       # Authentication modules
│   │   ├── __init__.py
│   │   ├── auth_factory.py        # Factory for creating auth clients
│   │   ├── oauth_client.py        # OAuth 2.0 authentication
│   │   └── basic_auth_client.py   # Basic authentication
│   │
│   ├── downloader/                 # API data downloaders
│   │   ├── __init__.py
│   │   ├── base_downloader.py     # Base class for all downloaders
│   │   ├── package_downloader.py
│   │   ├── iflow_downloader.py
│   │   ├── resource_downloader.py
│   │   ├── configuration_downloader.py
│   │   ├── message_mapping_downloader.py
│   │   ├── value_mapping_downloader.py
│   │   ├── script_collection_downloader.py
│   │   ├── security_downloader.py # Security APIs (credentials, certificates, etc.)
│   │   ├── partner_directory_downloader.py
│   │   ├── artifact_zip_downloader.py
│   │   ├── iflow_zip_extractor.py
│   │   ├── artifact_content_extractor.py
│   │   ├── readonly_package_extractor.py
│   │   └── discover_version_checker.py
│   │
│   ├── parsers/                    # JSON parsers (currently unused)
│   │   ├── __init__.py
│   │   ├── package_parser.py
│   │   ├── iflow_parser.py
│   │   ├── resource_parser.py
│   │   ├── configuration_parser.py
│   │   ├── message_mapping_parser.py
│   │   ├── value_mapping_parser.py
│   │   ├── script_collection_parser.py
│   │   ├── runtime_parser.py
│   │   └── security_parser.py
│   │
│   ├── analysers/                  # BPMN and content analyzers
│   │   ├── __init__.py
│   │   ├── environment_variable_scanner.py  # HC_ variable scanner
│   │   ├── bpmn_participant_extractor.py
│   │   ├── bpmn_channel_extractor.py
│   │   ├── bpmn_activity_extractor.py
│   │   ├── bpmn_script_extractor.py
│   │   ├── bpmn_message_mapping_extractor.py
│   │   ├── bpmn_xslt_mapping_extractor.py
│   │   ├── bpmn_content_modifier_extractor.py
│   │   ├── bpmn_timer_extractor.py
│   │   └── bpmn_process_activity_resolver.py
│   │
│   ├── database/                   # Database management
│   │   ├── __init__.py
│   │   └── db_manager.py          # Dynamic SQLite schema generator
│   │
│   ├── report_generators/          # Report generation framework
│   │   ├── __init__.py
│   │   ├── base_report.py         # Base class for all reports
│   │   ├── report_orchestrator.py # Main report coordinator
│   │   │
│   │   ├── formatters/            # Output formatters
│   │   │   ├── __init__.py
│   │   │   ├── html_formatter.py  # HTML report generator
│   │   │   └── excel_formatter.py # Excel workbook generator
│   │   │
│   │   └── report_types/          # Individual report type modules
│   │       ├── __init__.py
│   │       ├── package_version_comparison.py      # ✅ Implemented
│   │       ├── environment_variables.py           # ✅ Implemented
│   │       ├── package_statistics.py              # ✅ Implemented
│   │       ├── artifact_version_comparison.py     # 🔨 Stub
│   │       ├── certificate_validity.py            # 🔨 Stub
│   │       ├── systems_and_adapters.py            # 🔨 Stub
│   │       ├── iflow_statistics.py                # 🔨 Stub
│   │       ├── adapter_usage.py                   # 🔨 Stub
│   │       ├── value_mapping_stats.py             # 🔨 Stub
│   │       ├── neo_to_cf_migration.py             # 🔨 Stub
│   │       └── cross_region_migration.py          # 🔨 Stub
│   │
│   └── utils/                      # Utility modules
│       ├── __init__.py
│       ├── config.py              # Configuration management
│       ├── logger.py              # Logging setup
│       └── json_filter.py         # JSON filtering utilities
│
├── reports/                        # Generated reports output
│   └── .gitkeep
│
└── runs/                          # Runtime data (per tenant/timestamp)
    ├── .gitkeep
    └── {tenant_id}/
        └── {timestamp}/
            ├── ci_analyzer_{tenant}_{timestamp}.db    # SQLite database
            ├── ci_analyzer_{tenant}_{timestamp}.log   # Log file
            └── downloads/
                ├── json-files/                        # OData JSON responses
                ├── iflows/                           # IFlow artifacts
                │   ├── iflw-files/                  # IFLW files
                │   ├── groovy-scripts/              # Groovy scripts
                │   ├── java-scripts/                # JavaScript files
                │   ├── xslts/                       # XSLT files
                │   └── bpmn-json-files/             # BPMN analysis results
                ├── message-mappings/                 # Message mapping ZIPs
                ├── value-mappings/                   # Value mapping ZIPs
                ├── script-collections/               # Script collection ZIPs
                │   └── extracted-files/
                ├── partner-directory/                # Partner directory files
                └── read-only-packages/               # READ_ONLY package contents
```

## 🔄 Data Flow

```
1. DOWNLOAD PHASE
   main.py → downloader/* → API calls → downloads/json-files/

2. EXTRACTION PHASE
   downloaders → ZIP files → downloads/iflows/, script-collections/, etc.

3. ANALYSIS PHASE
   analysers/* → IFLW files → downloads/iflows/bpmn-json-files/

4. DATABASE PHASE
   database/db_manager.py → JSON files → SQLite database

5. REPORTING PHASE (New)
   report_generators/* → Database → HTML + Excel reports
```

## 📊 Report Generation Architecture

```
Report Generation Flow:
┌─────────────────────────────────────────────────┐
│  main.py --generate-reports                     │
└─────────────────┬───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│  ReportOrchestrator                             │
│  • Loads configuration                          │
│  • Instantiates all report modules              │
│  • Collects data from each report               │
│  • Aggregates summary metrics                   │
└─────────────────┬───────────────────────────────┘
                  ▼
         ┌────────┴────────┐
         ▼                  ▼
┌──────────────────┐  ┌──────────────────┐
│  HTML Formatter  │  │  Excel Formatter │
│  • Jinja2 temps  │  │  • openpyxl      │
│  • Bootstrap UI  │  │  • Multi-sheet   │
│  • Chart.js      │  │  • Formatted     │
│  • DataTables    │  │  • Raw data      │
└──────────────────┘  └──────────────────┘
         │                  │
         ▼                  ▼
    report.html        report.xlsx
```

## 🎯 Module Responsibilities

### Authentication (`src/auth/`)
- OAuth 2.0 token management
- Basic authentication
- Token refresh logic
- Multi-tenant support

### Downloaders (`src/downloader/`)
- API data retrieval
- Pagination handling
- Parallel downloads
- ZIP file extraction
- Content organization

### Analyzers (`src/analysers/`)
- BPMN XML parsing
- Script content extraction
- Environment variable scanning
- Relationship mapping

### Database (`src/database/`)
- Dynamic schema generation from JSON
- Bulk data import
- Query optimization
- Multi-tenant isolation

### Report Generators (`src/report_generators/`)
- **Base**: Common report functionality
- **Reports**: Individual report logic and queries
- **Formatters**: Output format generation (HTML, Excel)
- **Orchestrator**: Coordinates report generation

### Utilities (`src/utils/`)
- Configuration loading (.env)
- Structured logging
- JSON processing
- Common helpers

## 📝 Naming Conventions

### Files
- **Modules**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case()`
- **Constants**: `UPPER_SNAKE_CASE`

### Database
- **Tables**: `snake_case` (e.g., `package`, `iflow`, `bpmn_activity`)
- **Columns**: Keep original JSON field names (case-sensitive)
- **System columns**: `tenant_id`, `captured_at`

### Directories
- **Code**: `snake_case/`
- **Data**: `kebab-case/` (e.g., `json-files`, `groovy-scripts`)

## 🔐 Configuration

### Environment Variables (.env)
```ini
# Tenant Configuration
SAP_TENANT_ID=tenant_name
SAP_API_BASE_URL=https://...
SAP_AUTH_TYPE=OAUTH|BASIC

# Download Control
DOWNLOAD_PACKAGES=true
DOWNLOAD_IFLOWS=true
...

# Features
EXTRACT_IFLOW_CONTENT=true
PARSE_BPMN_CONTENT=true
...
```

## 📦 Dependencies

### Core
- `requests` - HTTP client
- `sqlite3` - Database (built-in)
- `pathlib` - File operations (built-in)

### Extraction
- `zipfile` - ZIP handling (built-in)
- `xml.etree.ElementTree` - XML parsing (built-in)

### Reporting (New)
- `jinja2` - HTML templating
- `openpyxl` - Excel generation
- `pandas` - Data manipulation (optional)

## 🚀 Execution Modes

### Standard Mode
```bash
python main.py
```
Downloads data, analyzes, and stores in database.

### Download Only
```bash
python main.py --save-only
```
or set `DOWNLOAD_ONLY=true` in .env

### Analyze Existing
```bash
ANALYZE_EXISTING=true
ANALYZE_RUN_TIMESTAMP=20260307_164253
```

### Generate Reports
```bash
python main.py --generate-reports --run-timestamp 20260307_164253
```

## 📈 Status Legend

- ✅ **Implemented**: Fully functional
- 🔨 **Stub**: Placeholder, needs implementation
- 🚧 **In Progress**: Currently being developed
- 📝 **Planned**: Designed, not yet started

## 🔄 Recent Changes

- **2026-03-07**: 
  - Created report generation framework
  - Moved stub report files to correct location
  - Implemented 3 priority reports
  - Organized project structure

## 📞 Support

For questions or issues, refer to:
- README.md - Project overview
- SETUP_GUIDE.md - Installation instructions
- Code comments - Inline documentation