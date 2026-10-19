# CI Analyzer Tool — Project Guide

Python desktop application for extracting data from SAP Cloud Integration (CI) subaccounts via OData APIs, storing it in SQLite, and generating HTML migration assessment reports (NEO→CF).

## Running the App

```bash
# Activate venv first
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux

# GUI (primary interface)
python ui.py

# CLI (headless, reads from .env)
python main.py
python main.py --log-level DEBUG
python main.py --api packages   # single API only
```

Before first run, copy `.env.example` → `.env` and fill in tenant credentials.

## Project Layout

```
ci-analyzer-tool/
├── main.py               # CLI orchestrator — 3-phase pipeline
├── ui.py                 # CustomTkinter desktop GUI
├── .env / .env.example   # Configuration (never commit .env)
├── runs/                 # Output: runs/{tenant_id}/{timestamp}/
│   └── {tenant}/
│       └── {timestamp}/
│           ├── downloads/json-files/    # OData API JSON responses
│           ├── downloads/iflows/        # .iflw XML + extracted JSON
│           ├── ci_analyzer_*.db         # SQLite database
│           ├── reports/*.html           # Generated HTML reports
│           └── *.log
└── src/
    ├── auth/             # OAuthClient, BasicAuthClient, auth_factory
    ├── downloader/       # BaseDownloader + 15 specific downloaders
    ├── analysers/        # IFLW XML analysers (channels, activities, etc.)
    ├── parsers/          # JSON parsers per artifact type
    ├── database/         # DynamicDatabaseManager (SQLite)
    ├── report_generators/# BaseReport + NeoToCFMigrationReport + formatters
    └── utils/            # Config, logger, ErrorCollector, FilenameSanitizer
```

## Execution Pipeline (FULL mode)

1. **Phase 1** — Download: Packages → IFlows → Resources/Configs → Security APIs → Partner Directory
2. **Phase 1.5** — ZIP extraction: IFlow ZIPs → `.iflw` XML files
3. **Phase 1.7** — Artifact content extraction: Script Collections, Message Mappings, Value Mappings
4. **Phase 1.9.x** — IFLW analysis: participants, channels, activities, scripts, timers, content modifiers, XSLT, env var scan
5. **Phase 2** — DB: DynamicDatabaseManager infers schema from JSON, imports all 28 table types, saves `download-errors.json`
6. **Phase 3** — Reports: `NeoToCFMigrationReport.generate()` → `NeoToCFFormatter.generate_html()` → HTML file

**REPORT_ONLY mode** skips Phases 1–2; reads from an existing `.db` specified by `REPORT_DB_PATH`.

## Key Patterns

### Authentication factory
```python
# src/auth/auth_factory.py
auth_client = create_auth_client(config)   # → OAuthClient | BasicAuthClient
```
CF subaccounts only support OAuth. Basic auth is NEO-only.

### Config singleton
```python
# src/utils/config.py
config = get_config()   # Loads .env, validates, returns Config singleton
```
Validation raises `ValueError` on startup for any misconfiguration — never silently continues.

### BaseDownloader pagination
```python
# src/downloader/base_downloader.py
# All OData downloaders use _fetch_all_pages() for $skip/$top pagination
```

### DynamicDatabaseManager
```python
# src/database/db_manager.py
# TABLE_NAME_MAP maps 28 JSON filenames → SQLite table names
# Schema is inferred from JSON key structure on first import
```

### ErrorCollector
```python
# src/utils/error_collector.py
# Centralized — collects errors from all download/extraction phases
# Saved as download-errors.json in json-files/ so it gets imported into DB
error_collector.add_error(package_id, artifact_type, error_code, error_type, message)
error_collector.save(json_files_dir)
```

### FilenameSanitizer
```python
# src/utils/filename_sanitizer.py
sanitize_chars(name)          # Replaces illegal Windows chars, no truncation
sanitize_source_name(name)    # Also truncates to 80 chars + hash suffix
# Use sanitize_chars() for scripts (env var scanner stores filename)
# Use sanitize_source_name() for schema/mapping files only
```

### BaseReport
```python
# src/report_generators/base_report.py
class MyReport(BaseReport):
    def generate(self) -> Dict[str, Any]: ...    # required
    def get_report_name(self) -> str: ...        # required
    def get_report_title(self) -> str: ...       # required
```

## Configuration Reference

All settings via `.env`. Key variables:

| Variable | Values | Notes |
|---|---|---|
| `SAP_TENANT_ID` | string | Used in run dir and DB filename |
| `SAP_TENANT_SHORT_NAME` | string | Short label for filenames |
| `SAP_SUBACCOUNT_TYPE` | `CF` / `NEO` | Affects auth options and cert mappings |
| `SAP_AUTH_TYPE` | `OAUTH` / `BASIC` | BASIC is NEO-only |
| `SAP_API_BASE_URL` | https://... | Must start with https:// |
| `EXECUTION_MODE` | `FULL` / `REPORT_ONLY` | REPORT_ONLY needs `REPORT_DB_PATH` |
| `REPORT_DB_PATH` | path/to/file.db | Required for REPORT_ONLY mode |
| `REPORT_NEO_TO_CF` | `true` / `false` | Whether to generate the migration report |
| `PARALLEL_DOWNLOADS` | 1–10 | ThreadPoolExecutor workers |
| `CLEANUP_DOWNLOADS` | `true` / `false` | Delete downloads/ after reports |
| `DISCOVER_BASE_URL` | https://... | Optional: SAP Discover version checking |

## Database Tables (28)

Mapped in `DynamicDatabaseManager.TABLE_NAME_MAP`:
- OData: `runtime`, `package`, `iflow`, `resource`, `configuration`, `message_mapping`, `value_mapping`, `script_collection`
- Security: `security_user_credential`, `security_oauth2_client_credential`, `security_secure_parameter`, `security_keystore_entry`, `security_certificate_user_mapping`, `security_access_policy`
- Partner: `partner_directory_binary_parameter`
- Misc: `environment_variable_check`, `package_discover_version`, `download_error`
- IFLW: `iflw_participant`, `iflw_channel`, `iflw_channel_property`, `iflw_activity`, `iflw_activity_property`, `iflw_groovy_script`, `iflw_message_mapping`, `iflw_xslt_mapping`, `iflw_content_modifier`, `iflw_timer`

## Reports

**Currently implemented:**
- `NeoToCFMigrationReport` (`src/report_generators/report_types/neo_to_cf_migration.py`) — comprehensive NEO→CF HTML report with SAP BTP styling, per-artifact and per-package readiness, systems/adapters, env vars, keystore, certificate mappings (NEO only), download errors

**Also implemented (older):**
- `PackageVersionComparison`, `EnvironmentVariables`, `PackageStatistics`

## Build & Release

Triggered by pushing a `v*.*.*` tag to `main`. GitHub Actions (`.github/workflows/build.yml`):

- **Windows**: PyInstaller `--onedir`, self-signed PowerShell cert (`WINDOWS_CERTIFICATE` + `WINDOWS_CERTIFICATE_PASSWORD` secrets), zipped as `CI-Analyzer-Windows.zip`
- **macOS**: PyInstaller `--onefile`, ad-hoc signed with `codesign -s -`, zipped as `CI-Analyzer-macOS.zip`
- **Release**: GitHub Release with both ZIPs + `ci-analyzer-codesign.cer` for Windows trust

```bash
# Trigger a release
git tag v1.2.3
git push origin v1.2.3
```

## Development Notes

- Python 3.11 required (used in venv and CI)
- No Docker image — previously planned, not implemented
- `testing-scripts/` contains ad-hoc helper scripts, not part of the main app
- `runs/` is gitignored except `.gitkeep`; output can be large
- IFLW files are SAP's proprietary XML format for integration flows (renamed from "bpmn" in recent refactor)
- Certificate-to-User mappings are a NEO-only API — always skipped for CF subaccounts
