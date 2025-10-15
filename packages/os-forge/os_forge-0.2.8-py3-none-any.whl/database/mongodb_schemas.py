"""
MongoDB Schemas for OS Forge
Comprehensive data models for storing hardening results, system information, and compliance data
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
import uuid

class RuleStatus(str, Enum):
    """Rule execution status"""
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    SKIP = "skip"

class SeverityLevel(str, Enum):
    """Rule severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class HardeningLevel(str, Enum):
    """Hardening levels"""
    BASIC = "basic"
    MODERATE = "moderate"
    STRICT = "strict"

class OSType(str, Enum):
    """Operating system types"""
    LINUX = "linux"
    WINDOWS = "windows"
    MACOS = "macos"

# Base MongoDB Document
class MongoDBDocument(BaseModel):
    """Base MongoDB document with common fields"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        validate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# System Information Schema
class SystemInfo(MongoDBDocument):
    """System information and capabilities"""
    hostname: str
    os_type: OSType
    os_version: str
    os_distribution: Optional[str] = None
    architecture: str
    kernel_version: Optional[str] = None
    package_manager: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    system_uptime: Optional[float] = None
    memory_total: Optional[int] = None
    memory_available: Optional[int] = None
    disk_total: Optional[int] = None
    disk_available: Optional[int] = None
    cpu_count: Optional[int] = None
    cpu_model: Optional[str] = None
    network_interfaces: List[Dict[str, Any]] = Field(default_factory=list)
    installed_packages: List[str] = Field(default_factory=list)
    running_services: List[str] = Field(default_factory=list)
    open_ports: List[int] = Field(default_factory=list)
    users: List[Dict[str, Any]] = Field(default_factory=list)
    groups: List[Dict[str, Any]] = Field(default_factory=list)
    last_scan_date: Optional[datetime] = None

# Rule Definition Schema
class RuleDefinition(MongoDBDocument):
    """Hardening rule definition"""
    rule_id: str = Field(..., unique=True)
    name: str
    description: str
    category: str
    os_types: List[OSType]
    severity: SeverityLevel
    levels: List[HardeningLevel]
    check_command: str
    remediate_command: str
    rollback_command: Optional[str] = None
    expected_value: Optional[str] = None
    rationale: Optional[str] = None
    references: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    is_active: bool = True
    version: str = "1.0"
    compliance_frameworks: List[str] = Field(default_factory=list)  # e.g., ["NTRO", "CIS", "NIST"]

# Hardening Result Schema
class HardeningResult(MongoDBDocument):
    """Individual rule execution result"""
    rule_id: str
    rule_name: str
    rule_category: str
    hostname: str
    os_type: OSType
    os_version: str
    hardening_level: HardeningLevel
    status: RuleStatus
    severity: SeverityLevel
    scan_session_id: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    expected_value: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    check_output: Optional[str] = None
    remediate_output: Optional[str] = None
    rollback_data: Optional[Dict[str, Any]] = None
    is_remediated: bool = False
    is_rollback_available: bool = False
    compliance_score: Optional[float] = None

# Scan Session Schema
class ScanSession(MongoDBDocument):
    """Complete hardening scan session"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hostname: str
    os_type: OSType
    os_version: str
    hardening_level: HardeningLevel
    category_filter: Optional[str] = None
    is_dry_run: bool = True
    start_time: datetime
    end_time: Optional[datetime] = None
    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    error_rules: int = 0
    skipped_rules: int = 0
    compliance_percentage: Optional[float] = None
    execution_summary: Dict[str, Any] = Field(default_factory=dict)
    system_info_id: Optional[str] = None  # Reference to SystemInfo
    results: List[str] = Field(default_factory=list)  # References to HardeningResult IDs
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

# Compliance Report Schema
class ComplianceReport(MongoDBDocument):
    """Compliance report and analysis"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_name: str
    report_type: str  # "html", "pdf", "json", "csv"
    hostname: str
    os_type: OSType
    scan_session_id: str
    generated_at: datetime
    report_period_start: datetime
    report_period_end: datetime
    compliance_framework: Optional[str] = None
    overall_score: float
    category_scores: Dict[str, float] = Field(default_factory=dict)
    severity_breakdown: Dict[str, int] = Field(default_factory=dict)
    level_breakdown: Dict[str, int] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    critical_issues: List[str] = Field(default_factory=list)
    report_content: Optional[str] = None  # For HTML reports
    report_file_path: Optional[str] = None  # For file-based reports
    report_metadata: Dict[str, Any] = Field(default_factory=dict)

# Rollback Operation Schema
class RollbackOperation(MongoDBDocument):
    """Rollback operation tracking"""
    operation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str
    rule_name: str
    hostname: str
    original_result_id: str  # Reference to HardeningResult
    rollback_command: str
    rollback_data: Dict[str, Any]
    executed_at: datetime
    status: RuleStatus
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    rollback_output: Optional[str] = None
    verified: bool = False
    verification_result: Optional[Dict[str, Any]] = None

# User Session Schema
class UserSession(MongoDBDocument):
    """User session tracking"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    login_time: datetime
    logout_time: Optional[datetime] = None
    is_active: bool = True
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    scan_sessions: List[str] = Field(default_factory=list)  # References to ScanSession IDs

# Configuration Schema
class SystemConfiguration(MongoDBDocument):
    """System configuration and settings"""
    config_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hostname: str
    os_type: OSType
    configuration_type: str  # "agent", "api", "cli", "frontend"
    settings: Dict[str, Any] = Field(default_factory=dict)
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    installed_packages: List[str] = Field(default_factory=list)
    service_configurations: Dict[str, Any] = Field(default_factory=dict)
    network_configurations: Dict[str, Any] = Field(default_factory=dict)
    security_policies: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

# Audit Log Schema
class AuditLog(MongoDBDocument):
    """Audit log for security events"""
    log_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str  # "login", "logout", "scan", "remediate", "rollback", "config_change"
    hostname: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    event_description: str
    event_data: Dict[str, Any] = Field(default_factory=dict)
    severity: SeverityLevel
    success: bool
    error_message: Optional[str] = None
    affected_resources: List[str] = Field(default_factory=list)
    compliance_impact: Optional[str] = None

# Collection Indexes Configuration
COLLECTION_INDEXES = {
    "system_info": [
        {"hostname": 1, "os_type": 1},
        {"last_scan_date": -1},
        {"os_type": 1, "os_version": 1}
    ],
    "rule_definitions": [
        {"rule_id": 1},
        {"category": 1, "os_types": 1},
        {"severity": 1, "levels": 1},
        {"is_active": 1}
    ],
    "hardening_results": [
        {"rule_id": 1, "hostname": 1},
        {"scan_session_id": 1},
        {"status": 1, "severity": 1},
        {"created_at": -1},
        {"hostname": 1, "os_type": 1}
    ],
    "scan_sessions": [
        {"session_id": 1},
        {"hostname": 1, "created_at": -1},
        {"os_type": 1, "hardening_level": 1},
        {"start_time": -1}
    ],
    "compliance_reports": [
        {"report_id": 1},
        {"hostname": 1, "generated_at": -1},
        {"scan_session_id": 1},
        {"compliance_framework": 1}
    ],
    "rollback_operations": [
        {"operation_id": 1},
        {"rule_id": 1, "hostname": 1},
        {"original_result_id": 1},
        {"executed_at": -1}
    ],
    "user_sessions": [
        {"session_id": 1},
        {"user_id": 1, "is_active": 1},
        {"login_time": -1}
    ],
    "system_configurations": [
        {"config_id": 1},
        {"hostname": 1, "configuration_type": 1},
        {"is_active": 1}
    ],
    "audit_logs": [
        {"log_id": 1},
        {"hostname": 1, "event_type": 1},
        {"created_at": -1},
        {"severity": 1, "success": 1}
    ]
}
