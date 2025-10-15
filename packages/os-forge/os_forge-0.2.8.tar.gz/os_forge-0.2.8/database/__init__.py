"""
Database module for OS Forge - MongoDB Only
"""

from .manager import db_manager, init_db, get_db
from .mongodb_config import mongodb_config
from .mongodb_manager import mongodb_manager
from .mongodb_schemas import (
    SystemInfo, HardeningResult, ScanSession, ComplianceReport,
    RollbackOperation, UserSession, SystemConfiguration, AuditLog,
    OSType, RuleStatus, SeverityLevel, HardeningLevel
)

__all__ = [
    'db_manager', 'init_db', 'get_db',
    'mongodb_config', 'mongodb_manager',
    'SystemInfo', 'HardeningResult', 'ScanSession', 'ComplianceReport',
    'RollbackOperation', 'UserSession', 'SystemConfiguration', 'AuditLog',
    'OSType', 'RuleStatus', 'SeverityLevel', 'HardeningLevel'
]

