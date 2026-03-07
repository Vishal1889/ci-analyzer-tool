# SAP Cloud Integration Analyzer Tool

A Python-based tool to extract data from SAP Cloud Integration subaccounts via OData APIs, store it in a SQLite database, and generate analytical reports.

## Features

- 📥 **API Data Extraction**: Download integration content from SAP Cloud Integration APIs
- 💾 **SQLite Storage**: Store data in a local SQLite database with comprehensive schema
- 📊 **Analytics**: Generate insights from integration artifacts
- 📝 **Detailed Logging**: Multi-level logging (TRACE, DEBUG, INFO, WARNING, ERROR)
- 🔐 **OAuth Authentication**: Secure API access using OAuth 2.0
- 🎯 **Incremental Approach**: Support for API-by-API implementation

## Project Structure

```
ci-analyzer-tool/
├── src/                    # Source code
│   ├── auth/              # OAuth authentication
│   ├── downloader/        # API downloaders
│   ├── parsers/           # Response parsers
│   ├── database/          # Database management
│   └── utils/             # Utilities (logging, helpers)
├── downloads/             # API response storage (JSON)
├── logs/                  # Log files
├── reports/               # Generated reports
├── tests/                 # Unit tests
├── .env.example           # Configuration template
├── requirements.txt       # Python dependencies
└── main.py               # Entry point
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ci-analyzer-tool
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # Copy the example configuration
   copy .env.example .env
   
   # Edit .env and fill in your SAP Cloud Integration credentials
   ```

## Configuration

Edit the `.env` file with your SAP Cloud Integration details:

```properties
# Tenant Information
SAP_TENANT_ID=your-tenant-name
SAP_TENANT_SHORT_NAME=your-tenant

# OAuth Configuration
SAP_OAUTH_TOKEN_URL=https://your-tenant.authentication.region.hana.ondemand.com/oauth/token
SAP_CLIENT_ID=your_client_id
SAP_CLIENT_SECRET=your_client_secret

# API Base URL
SAP_API_BASE_URL=https://your-tenant-tmn.region.hana.ondemand.com/api/v1
```

## Usage

```bash
# Run the analyzer
python main.py

# Run specific API extraction (when implemented)
python main.py --api packages

# Enable trace logging
python main.py --log-level TRACE
```

## Database Schema

The tool uses a comprehensive SQLite schema based on SAP Cloud Integration data model:

- **Core Tables**: package, iflow, message_mapping, script_collection, value_mapping
- **Configuration**: configuration, resource
- **Runtime**: runtime
- **BPMN Analysis**: bpmn_activity, bpmn_channel, bpmn_participant, etc.
- **Security**: security_keystore_entry, security_oauth2_client_credential, etc.

See `reference files/reference_database.db` for complete schema.

## Logging

Logs are stored in the `logs/` directory with the format:
- Filename: `{tenant_id}_ci_analyzer_YYYYMMDD_HHMMSS.log`
- Levels: TRACE, DEBUG, INFO, WARNING, ERROR
- Console output: INFO and above
- File output: All levels

## Development Roadmap

### Phase 1: Foundation ✅
- [x] Project structure
- [x] Configuration management
- [ ] OAuth authentication
- [ ] Logging infrastructure
- [ ] Database schema

### Phase 2: API Integration (Incremental)
- [ ] Package API
- [ ] Integration Flow API
- [ ] Configuration API
- [ ] Runtime Artifacts API
- [ ] Security APIs

### Phase 3: Analysis & Reporting
- [ ] Database views
- [ ] Data analysis queries
- [ ] Report generation (HTML, CSV, JSON)

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src
```

## Contributing

1. Follow the incremental API-by-API approach
2. Add tests for new functionality
3. Update documentation
4. Follow PEP 8 style guidelines

## License

[Specify your license here]

## Support

For issues and questions, please create an issue in the repository.

## References

- [SAP Cloud Integration OData API Documentation](https://help.sap.com/docs/SAP_INTEGRATION_SUITE/51ab953548be4459bfe8539ecaeee98d/d1679a80543f46509a7329243b595bdb.html)
- [SAP Integration Suite](https://help.sap.com/docs/SAP_INTEGRATION_SUITE)