OS Forge
========

Multi-Platform System Hardening Tool with NTRO SIH25237 Compliance
- **394 Hardening Rules**: Linux (278), Windows (93), macOS (23)
- **100% NTRO SIH25237 Compliant**: Complete Annexure A & B coverage
- **MongoDB Integration**: Secure cloud-native database support

Installation
------------

```bash
pip install os-forge
```

MongoDB Setup (Required)
------------------------

```bash
# Set environment variables
export MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority"
export MONGODB_DATABASE="Os-forge"
export MONGODB_COLLECTION="detailsforOS"
```

CLI Help
--------

```bash
os-forge --help
```

Common Commands
---------------

```bash
# Show system info and rule counts
os-forge info

# Run checks (no changes)
os-forge check --level basic --dry-run

# Apply hardening rules
os-forge check --level moderate

# Generate compliance reports
os-forge report
os-forge pdf-report

# MongoDB operations
mongodb-migrate --help
```

Platforms
---------

**Linux**: 278 rules covering filesystem, services, network, SSH, auditing
**Windows**: 93 rules covering account policies, firewall, audit, services  
**macOS**: 23 rules covering system preferences, FileVault, firewall

Notes
-----

- Commands work identically across Linux, Windows, and macOS
- MongoDB Atlas recommended for cloud deployment
- Full documentation: `os-forge --help`
