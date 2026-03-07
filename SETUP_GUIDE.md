# SAP Cloud Integration Analyzer Tool - Setup Guide

## Quick Start

### 1. Prerequisites

- Python 3.8 or higher
- SAP Cloud Integration tenant access
- OAuth client credentials (Client ID and Client Secret)

### 2. Installation Steps

```bash
# 1. Navigate to project directory
cd ci-analyzer-tool

# 2. Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env with your SAP Cloud Integration credentials
```

### 3. Configuration

Edit the `.env` file with your SAP Cloud Integration details:

```properties
# Required Settings
SAP_TENANT_ID=your-tenant-name
SAP_TENANT_SHORT_NAME=yourtenant
SAP_OAUTH_TOKEN_URL=https://your-tenant.authentication.region.hana.ondemand.com/oauth/token
SAP_CLIENT_ID=your_client_id
SAP_CLIENT_SECRET=your_client_secret
SAP_API_BASE_URL=https://your-tenant-tmn.region.hana.ondemand.com/api/v1

# Optional Settings
LOG_LEVEL=INFO
DATABASE_PATH=./ci_analyzer.db
API_TIMEOUT=30
```

### 4. Verify Installation

```bash
# Test the installation
python main.py --version

# Output should be:
# CI Analyzer Tool v0.1.0
```

## Usage Examples

### Basic Usage

```bash
# Download and analyze all packages
python main.py

# Download packages only (specific API)
python main.py --api packages

# Enable detailed logging
python main.py --log-level DEBUG

# Enable API trace logging (very detailed)
python main.py --log-level TRACE
```

### Advanced Usage

```bash
# Only download and save JSON (don't process)
python main.py --api packages --save-only

# Parse previously downloaded JSON files
python main.py --api packages --parse-and-store
```

## Getting OAuth Credentials

### From SAP BTP Cockpit

1. Navigate to your SAP BTP subaccount
2. Go to **Security** → **OAuth**
3. Create a new OAuth client with:
   - Grant Type: Client Credentials
   - Scopes: Required API scopes for Integration Suite
4. Copy the Client ID and Client Secret

### From Cloud Integration UI

1. Navigate to Cloud Integration Monitor
2. Go to **Settings** → **Security Material**
3. Create OAuth2 Client Credentials artifact
4. Use the credentials in your `.env` file

## Project Structure

```
ci-analyzer-tool/
├── src/
│   ├── auth/              # OAuth authentication
│   │   └── oauth_client.py
│   ├── downloader/        # API downloaders
│   │   ├── base_downloader.py
│   │   └── package_downloader.py
│   ├── parsers/           # Response parsers
│   │   └── package_parser.py
│   ├── database/          # Database management
│   │   ├── schema.sql
│   │   └── db_manager.py
│   └── utils/             # Utilities
│       ├── config.py
│       └── logger.py
├── downloads/             # Downloaded JSON files
├── logs/                  # Log files
├── reports/               # Generated reports
├── main.py               # Entry point
├── requirements.txt      # Dependencies
└── .env                  # Configuration (create from .env.example)
```

## Output

### Downloaded Data
- Location: `downloads/`
- Format: JSON files with OData responses
- Example: `packages.json`

### Database
- Location: `./ci_analyzer.db` (configurable)
- Format: SQLite database
- Tables: 25+ tables for all integration artifacts

### Logs
- Location: `logs/`
- Format: `{tenant_id}_ci_analyzer_YYYYMMDD_HHMMSS.log`
- Levels: TRACE, DEBUG, INFO, WARNING, ERROR

## Troubleshooting

### Error: "Required environment variable ... is not set"
- Ensure `.env` file exists and contains all required variables
- Check that variable names match exactly (case-sensitive)

### Error: "Failed to acquire OAuth token"
- Verify OAuth token URL is correct
- Check Client ID and Client Secret
- Ensure OAuth client has required scopes

### Error: "Connection timeout"
- Check network connectivity to SAP Cloud Integration
- Increase `API_TIMEOUT` in `.env`
- Verify firewall/proxy settings

### Error: "Database is locked"
- Close any applications accessing the database
- Ensure only one instance of the tool is running

## Next Steps

After successful setup:

1. **Run initial extraction**: `python main.py --api packages`
2. **Check logs**: Review log file in `logs/` directory
3. **Verify database**: Use SQLite browser to view `ci_analyzer.db`
4. **Add more APIs**: Extend tool to download other artifact types

## Support

For issues and questions:
- Check log files in `logs/` directory
- Review error messages carefully
- Consult SAP Cloud Integration API documentation

## Development

To extend the tool:

1. **Add new API downloader**: Create new class in `src/downloader/`
2. **Add parser**: Create corresponding parser in `src/parsers/`
3. **Update main.py**: Add new API to orchestration logic
4. **Test**: Run with `--save-only` first to verify API calls

## References

- [SAP Cloud Integration API Documentation](https://api.sap.com/package/CloudIntegrationAPI/overview)
- [OAuth 2.0 Client Credentials Flow](https://oauth.net/2/grant-types/client-credentials/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)