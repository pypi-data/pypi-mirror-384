"""
MongoDB-Only Database Manager for OS Forge
Simplified database operations using only MongoDB
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

from .mongodb_manager import mongodb_manager
from .mongodb_schemas import (
    SystemInfo, HardeningResult, ScanSession, ComplianceReport,
    OSType, RuleStatus, SeverityLevel, HardeningLevel
)

logger = logging.getLogger(__name__)

class DatabaseManager:
    """MongoDB-only database manager"""
    
    def __init__(self):
        self.manager = mongodb_manager
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize MongoDB connection"""
        if not self.manager.config.is_enabled():
            logger.info("MongoDB is disabled. Skipping initialization.")
            return False
        
        try:
            if not self.initialized:
                success = await self.manager.initialize()
                if success:
                    self.initialized = True
                    logger.info("MongoDB database initialized successfully")
                else:
                    logger.error("MongoDB initialization failed")
                    return False
            return True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
    
    # Hardening Result Operations
    async def create_hardening_result(self, result_data: Dict[str, Any]) -> str:
        """Create hardening result"""
        if not self.manager.config.is_enabled():
            return None
        
        try:
            await self.initialize()
            result = HardeningResult(**result_data)
            return await self.manager.create_hardening_result(result)
        except Exception as e:
            logger.warning(f"Failed to create hardening result: {e}")
            return None
    
    async def get_hardening_results(self, hostname: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get hardening results for a host"""
        if not self.manager.config.is_enabled():
            return []
        
        try:
            await self.initialize()
            results = await self.manager.get_recent_results(hostname, limit)
            return [result.dict() for result in results]
        except Exception as e:
            logger.warning(f"Failed to get hardening results: {e}")
            return []
    
    async def get_hardening_results_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get hardening results for a scan session"""
        await self.initialize()
        results = await self.manager.get_hardening_results(session_id)
        return [result.dict() for result in results]
    
    # Scan Session Operations
    async def create_scan_session(self, session_data: Dict[str, Any]) -> str:
        """Create scan session"""
        await self.initialize()
        session = ScanSession(**session_data)
        return await self.manager.create_scan_session(session)
    
    async def update_scan_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update scan session"""
        await self.initialize()
        return await self.manager.update_scan_session(session_id, updates)
    
    async def get_scan_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get scan session"""
        await self.initialize()
        session = await self.manager.get_scan_session(session_id)
        return session.dict() if session else None
    
    async def get_scan_sessions(self, hostname: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get scan sessions for a host"""
        await self.initialize()
        sessions = await self.manager.get_scan_sessions(hostname, limit)
        return [session.dict() for session in sessions]
    
    # System Info Operations
    async def create_system_info(self, system_data: Dict[str, Any]) -> str:
        """Create system information"""
        await self.initialize()
        system_info = SystemInfo(**system_data)
        return await self.manager.create_system_info(system_info)
    
    async def get_system_info(self, hostname: str, os_type: str) -> Optional[Dict[str, Any]]:
        """Get system information"""
        await self.initialize()
        system_info = await self.manager.get_system_info(hostname, os_type)
        return system_info.dict() if system_info else None
    
    # Compliance Report Operations
    async def create_compliance_report(self, report_data: Dict[str, Any]) -> str:
        """Create compliance report"""
        await self.initialize()
        report = ComplianceReport(**report_data)
        return await self.manager.create_compliance_report(report)
    
    async def get_compliance_reports(self, hostname: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get compliance reports"""
        await self.initialize()
        reports = await self.manager.get_compliance_reports(hostname, limit)
        return [report.dict() for report in reports]
    
    # Rollback Operations
    async def create_rollback_operation(self, operation_data: Dict[str, Any]) -> str:
        """Create rollback operation"""
        await self.initialize()
        from .mongodb_schemas import RollbackOperation
        operation = RollbackOperation(**operation_data)
        return await self.manager.create_rollback_operation(operation)
    
    async def get_rollback_operations(self, hostname: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get rollback operations"""
        await self.initialize()
        operations = await self.manager.get_rollback_operations(hostname, limit)
        return [operation.dict() for operation in operations]
    
    # Audit Log Operations
    async def create_audit_log(self, log_data: Dict[str, Any]) -> str:
        """Create audit log entry"""
        await self.initialize()
        from .mongodb_schemas import AuditLog
        log = AuditLog(**log_data)
        return await self.manager.create_audit_log(log)
    
    async def get_audit_logs(self, hostname: str, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit logs"""
        await self.initialize()
        logs = await self.manager.get_audit_logs(hostname, event_type, limit)
        return [log.dict() for log in logs]
    
    # Analytics and Reporting
    async def get_compliance_summary(self, hostname: str, days: int = 30) -> Dict[str, Any]:
        """Get compliance summary"""
        await self.initialize()
        return await self.manager.get_compliance_summary(hostname, days)
    
    async def get_category_compliance(self, hostname: str) -> Dict[str, Dict[str, Any]]:
        """Get compliance by category"""
        await self.initialize()
        return await self.manager.get_category_compliance(hostname)
    
    # Cleanup Operations
    async def cleanup_old_data(self, days: int = 90):
        """Clean up old data"""
        await self.initialize()
        await self.manager.cleanup_old_data(days)
    
    async def close(self):
        """Close database connections"""
        await self.manager.close()
        self.initialized = False

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions for backward compatibility
async def init_db():
    """Initialize database"""
    return await db_manager.initialize()

async def get_db():
    """Get database manager"""
    return db_manager
