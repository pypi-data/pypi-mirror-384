"""
MongoDB Data Access Layer for OS Forge
Provides async and sync methods for database operations
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, OperationFailure
import logging

from .mongodb_config import mongodb_config
from .mongodb_schemas import (
    SystemInfo, RuleDefinition, HardeningResult, ScanSession,
    ComplianceReport, RollbackOperation, UserSession, 
    SystemConfiguration, AuditLog, COLLECTION_INDEXES
)

logger = logging.getLogger(__name__)

class MongoDBManager:
    """MongoDB database manager with async and sync operations"""
    
    def __init__(self):
        self.config = mongodb_config
        self._collections = {}
    
    async def initialize(self):
        """Initialize MongoDB connection and create indexes"""
        if not self.config.is_enabled():
            logger.info("MongoDB is disabled. Skipping initialization.")
            return True
            
        try:
            # Test connection
            if not await self.config.test_connection():
                raise Exception("Failed to connect to MongoDB")
            
            # Get database
            db = await self.config.get_database()
            
            # Create collections and indexes
            for collection_name, indexes in COLLECTION_INDEXES.items():
                collection = db[collection_name]
                self._collections[collection_name] = collection
                
                # Create indexes
                for index in indexes:
                    try:
                        await collection.create_index(list(index.keys()), background=True)
                    except Exception as e:
                        logger.warning(f"Failed to create index {index} for {collection_name}: {e}")
            
            logger.info("MongoDB initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"MongoDB initialization failed: {e}")
            return False
    
    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """Get MongoDB collection"""
        if not self.config.is_enabled():
            raise RuntimeError("MongoDB is not enabled. Set MONGODB_URI environment variable.")
        return self._collections.get(collection_name)
    
    # System Info Operations
    async def create_system_info(self, system_info: SystemInfo) -> str:
        """Create or update system information"""
        collection = self.get_collection("system_info")
        system_info.updated_at = datetime.utcnow()
        
        try:
            result = await collection.insert_one(system_info.dict(by_alias=True))
            return str(result.inserted_id)
        except DuplicateKeyError:
            # Update existing record
            await collection.update_one(
                {"hostname": system_info.hostname, "os_type": system_info.os_type},
                {"$set": system_info.dict(by_alias=True, exclude={"id", "created_at"})}
            )
            return system_info.id
    
    async def get_system_info(self, hostname: str, os_type: str) -> Optional[SystemInfo]:
        """Get system information"""
        collection = self.get_collection("system_info")
        doc = await collection.find_one({"hostname": hostname, "os_type": os_type})
        return SystemInfo(**doc) if doc else None
    
    # Rule Definition Operations
    async def create_rule_definition(self, rule: RuleDefinition) -> str:
        """Create rule definition"""
        collection = self.get_collection("rule_definitions")
        result = await collection.insert_one(rule.dict(by_alias=True))
        return str(result.inserted_id)
    
    async def get_rule_definition(self, rule_id: str) -> Optional[RuleDefinition]:
        """Get rule definition"""
        collection = self.get_collection("rule_definitions")
        doc = await collection.find_one({"rule_id": rule_id})
        return RuleDefinition(**doc) if doc else None
    
    async def get_rules_by_category(self, category: str, os_type: str) -> List[RuleDefinition]:
        """Get rules by category and OS type"""
        collection = self.get_collection("rule_definitions")
        cursor = collection.find({
            "category": category,
            "os_types": os_type,
            "is_active": True
        })
        return [RuleDefinition(**doc) async for doc in cursor]
    
    # Hardening Result Operations
    async def create_hardening_result(self, result: HardeningResult) -> str:
        """Create hardening result"""
        collection = self.get_collection("hardening_results")
        result_dict = result.dict(by_alias=True)
        result_dict["created_at"] = datetime.utcnow()
        result_dict["updated_at"] = datetime.utcnow()
        
        db_result = await collection.insert_one(result_dict)
        return str(db_result.inserted_id)
    
    async def get_hardening_results(self, scan_session_id: str) -> List[HardeningResult]:
        """Get hardening results for a scan session"""
        collection = self.get_collection("hardening_results")
        cursor = collection.find({"scan_session_id": scan_session_id})
        return [HardeningResult(**doc) async for doc in cursor]
    
    async def get_recent_results(self, hostname: str, limit: int = 100) -> List[HardeningResult]:
        """Get recent hardening results for a host"""
        collection = self.get_collection("hardening_results")
        cursor = collection.find({"hostname": hostname}).sort("created_at", -1).limit(limit)
        return [HardeningResult(**doc) async for doc in cursor]
    
    # Scan Session Operations
    async def create_scan_session(self, session: ScanSession) -> str:
        """Create scan session"""
        collection = self.get_collection("scan_sessions")
        session_dict = session.dict(by_alias=True)
        session_dict["created_at"] = datetime.utcnow()
        session_dict["updated_at"] = datetime.utcnow()
        
        result = await collection.insert_one(session_dict)
        return str(result.inserted_id)
    
    async def update_scan_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update scan session"""
        collection = self.get_collection("scan_sessions")
        updates["updated_at"] = datetime.utcnow()
        
        result = await collection.update_one(
            {"session_id": session_id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    async def get_scan_session(self, session_id: str) -> Optional[ScanSession]:
        """Get scan session"""
        collection = self.get_collection("scan_sessions")
        doc = await collection.find_one({"session_id": session_id})
        return ScanSession(**doc) if doc else None
    
    async def get_scan_sessions(self, hostname: str, limit: int = 50) -> List[ScanSession]:
        """Get scan sessions for a host"""
        collection = self.get_collection("scan_sessions")
        cursor = collection.find({"hostname": hostname}).sort("start_time", -1).limit(limit)
        return [ScanSession(**doc) async for doc in cursor]
    
    # Compliance Report Operations
    async def create_compliance_report(self, report: ComplianceReport) -> str:
        """Create compliance report"""
        collection = self.get_collection("compliance_reports")
        report_dict = report.dict(by_alias=True)
        report_dict["created_at"] = datetime.utcnow()
        report_dict["updated_at"] = datetime.utcnow()
        
        result = await collection.insert_one(report_dict)
        return str(result.inserted_id)
    
    async def get_compliance_reports(self, hostname: str, limit: int = 20) -> List[ComplianceReport]:
        """Get compliance reports for a host"""
        collection = self.get_collection("compliance_reports")
        cursor = collection.find({"hostname": hostname}).sort("generated_at", -1).limit(limit)
        return [ComplianceReport(**doc) async for doc in cursor]
    
    # Rollback Operations
    async def create_rollback_operation(self, operation: RollbackOperation) -> str:
        """Create rollback operation"""
        collection = self.get_collection("rollback_operations")
        operation_dict = operation.dict(by_alias=True)
        operation_dict["created_at"] = datetime.utcnow()
        operation_dict["updated_at"] = datetime.utcnow()
        
        result = await collection.insert_one(operation_dict)
        return str(result.inserted_id)
    
    async def get_rollback_operations(self, hostname: str, limit: int = 50) -> List[RollbackOperation]:
        """Get rollback operations for a host"""
        collection = self.get_collection("rollback_operations")
        cursor = collection.find({"hostname": hostname}).sort("executed_at", -1).limit(limit)
        return [RollbackOperation(**doc) async for doc in cursor]
    
    # Audit Log Operations
    async def create_audit_log(self, log: AuditLog) -> str:
        """Create audit log entry"""
        collection = self.get_collection("audit_logs")
        log_dict = log.dict(by_alias=True)
        log_dict["created_at"] = datetime.utcnow()
        log_dict["updated_at"] = datetime.utcnow()
        
        result = await collection.insert_one(log_dict)
        return str(result.inserted_id)
    
    async def get_audit_logs(self, hostname: str, event_type: Optional[str] = None, limit: int = 100) -> List[AuditLog]:
        """Get audit logs for a host"""
        collection = self.get_collection("audit_logs")
        query = {"hostname": hostname}
        if event_type:
            query["event_type"] = event_type
        
        cursor = collection.find(query).sort("created_at", -1).limit(limit)
        return [AuditLog(**doc) async for doc in cursor]
    
    # Analytics and Reporting
    async def get_compliance_summary(self, hostname: str, days: int = 30) -> Dict[str, Any]:
        """Get compliance summary for a host"""
        collection = self.get_collection("hardening_results")
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {"$match": {"hostname": hostname, "created_at": {"$gte": start_date}}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "avg_execution_time": {"$avg": "$execution_time"}
            }},
            {"$group": {
                "_id": None,
                "status_counts": {"$push": {"status": "$_id", "count": "$count"}},
                "total_rules": {"$sum": "$count"},
                "avg_execution_time": {"$avg": "$avg_execution_time"}
            }}
        ]
        
        result = await collection.aggregate(pipeline).to_list(1)
        return result[0] if result else {}
    
    async def get_category_compliance(self, hostname: str) -> Dict[str, Dict[str, Any]]:
        """Get compliance by category"""
        collection = self.get_collection("hardening_results")
        
        pipeline = [
            {"$match": {"hostname": hostname}},
            {"$group": {
                "_id": "$rule_category",
                "total": {"$sum": 1},
                "passed": {"$sum": {"$cond": [{"$eq": ["$status", "pass"]}, 1, 0]}},
                "failed": {"$sum": {"$cond": [{"$eq": ["$status", "fail"]}, 1, 0]}},
                "errors": {"$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}}
            }},
            {"$addFields": {
                "compliance_percentage": {
                    "$multiply": [
                        {"$divide": ["$passed", "$total"]},
                        100
                    ]
                }
            }}
        ]
        
        results = await collection.aggregate(pipeline).to_list(None)
        return {result["_id"]: result for result in results}
    
    # Cleanup Operations
    async def cleanup_old_data(self, days: int = 90):
        """Clean up old data"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        collections_to_clean = [
            "hardening_results",
            "scan_sessions", 
            "compliance_reports",
            "rollback_operations",
            "audit_logs"
        ]
        
        for collection_name in collections_to_clean:
            collection = self.get_collection(collection_name)
            result = await collection.delete_many({"created_at": {"$lt": cutoff_date}})
            logger.info(f"Cleaned up {result.deleted_count} old records from {collection_name}")
    
    async def close(self):
        """Close MongoDB connections"""
        await self.config.close_connections()

# Global MongoDB manager instance
mongodb_manager = MongoDBManager()
