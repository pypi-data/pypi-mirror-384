"""
Migration utility to migrate data from SQLite to MongoDB
"""

import asyncio
import sqlite3
from datetime import datetime
from typing import List, Dict, Any
import logging

from .mongodb_manager import mongodb_manager
from .mongodb_schemas import (
    SystemInfo, HardeningResult, ScanSession, ComplianceReport,
    OSType, RuleStatus, SeverityLevel, HardeningLevel
)

logger = logging.getLogger(__name__)

class SQLiteToMongoDBMigrator:
    """Migrate data from SQLite to MongoDB"""
    
    def __init__(self, sqlite_db_path: str = "policy_guard.db"):
        self.sqlite_db_path = sqlite_db_path
        self.mongodb_manager = mongodb_manager
    
    async def migrate_all_data(self) -> Dict[str, int]:
        """Migrate all data from SQLite to MongoDB"""
        migration_results = {}
        
        try:
            # Initialize MongoDB
            await self.mongodb_manager.initialize()
            
            # Migrate hardening results
            migration_results["hardening_results"] = await self.migrate_hardening_results()
            
            # Create system info from migrated data
            migration_results["system_info"] = await self.create_system_info_from_results()
            
            # Create scan sessions from migrated data
            migration_results["scan_sessions"] = await self.create_scan_sessions_from_results()
            
            logger.info(f"Migration completed successfully: {migration_results}")
            return migration_results
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    async def migrate_hardening_results(self) -> int:
        """Migrate hardening results from SQLite to MongoDB"""
        conn = sqlite3.connect(self.sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Get all hardening results
            cursor.execute("SELECT * FROM hardening_results")
            rows = cursor.fetchall()
            
            migrated_count = 0
            
            for row in rows:
                # Convert SQLite row to MongoDB document
                # SQLite row format: (id, rule_id, hostname, description, severity, status, old_value, new_value, timestamp, rollback_data)
                result_data = {
                    "rule_id": row[1],  # rule_id
                    "rule_name": row[3],  # description
                    "rule_category": "unknown",  # Default category
                    "hostname": row[2],  # hostname
                    "os_type": OSType.LINUX,  # Default to Linux
                    "os_version": "unknown",
                    "hardening_level": HardeningLevel.MODERATE,  # Default level
                    "status": RuleStatus(row[5]),  # status
                    "severity": SeverityLevel(row[4]) if row[4] in ["critical", "high", "medium", "low"] else SeverityLevel.MEDIUM,  # severity
                    "old_value": row[6],  # old_value
                    "new_value": row[7],  # new_value
                    "error_message": None,
                    "execution_time": None,
                    "check_output": None,
                    "remediate_output": None,
                    "rollback_data": self._parse_rollback_data(row[9]),  # rollback_data
                    "is_remediated": row[5] == "pass",  # status
                    "is_rollback_available": bool(row[9]),  # rollback_data
                    "compliance_score": None,
                    "scan_session_id": f"migrated_{row[0]}",  # id
                    "created_at": datetime.fromisoformat(row[8]),  # timestamp
                    "updated_at": datetime.fromisoformat(row[8])  # timestamp
                }
                
                # Create HardeningResult document
                result = HardeningResult(**result_data)
                await self.mongodb_manager.create_hardening_result(result)
                migrated_count += 1
            
            logger.info(f"Migrated {migrated_count} hardening results")
            return migrated_count
            
        finally:
            conn.close()
    
    def _parse_rollback_data(self, rollback_data: str) -> Dict[str, Any]:
        """Parse rollback data from SQLite format"""
        if not rollback_data:
            return {}
        
        try:
            import json
            # Try to parse as JSON
            parsed = json.loads(rollback_data)
            if isinstance(parsed, str):
                # If it's a string command, convert to dict format
                return {
                    "rollback_command": parsed,
                    "original_value": None,
                    "timestamp": datetime.utcnow().isoformat()
                }
            return parsed
        except:
            # If parsing fails, treat as command string
            return {
                "rollback_command": rollback_data,
                "original_value": None,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def create_system_info_from_results(self) -> int:
        """Create system info from migrated hardening results"""
        # Get unique hostnames from results
        collection = self.mongodb_manager.get_collection("hardening_results")
        hosts = await collection.distinct("hostname")
        
        created_count = 0
        
        for hostname in hosts:
            # Create system info for each host
            system_info_data = {
                "hostname": hostname,
                "os_type": OSType.LINUX,
                "os_version": "unknown",
                "os_distribution": "unknown",
                "architecture": "unknown",
                "kernel_version": None,
                "package_manager": None,
                "capabilities": [],
                "system_uptime": None,
                "memory_total": None,
                "memory_available": None,
                "disk_total": None,
                "disk_available": None,
                "cpu_count": None,
                "cpu_model": None,
                "network_interfaces": [],
                "installed_packages": [],
                "running_services": [],
                "open_ports": [],
                "users": [],
                "groups": [],
                "last_scan_date": datetime.utcnow(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            system_info = SystemInfo(**system_info_data)
            await self.mongodb_manager.create_system_info(system_info)
            created_count += 1
        
        logger.info(f"Created {created_count} system info records")
        return created_count
    
    async def create_scan_sessions_from_results(self) -> int:
        """Create scan sessions from migrated hardening results"""
        # Group results by scan_session_id
        collection = self.mongodb_manager.get_collection("hardening_results")
        
        # Get unique session IDs
        session_ids = await collection.distinct("scan_session_id")
        
        created_count = 0
        
        for session_id in session_ids:
            # Get results for this session
            results = await self.mongodb_manager.get_hardening_results(session_id)
            
            if not results:
                continue
            
            # Get first result for session metadata
            first_result = results[0]
            
            # Count results by status
            status_counts = {}
            for result in results:
                status_counts[result.status] = status_counts.get(result.status, 0) + 1
            
            # Calculate compliance percentage
            total_rules = len(results)
            passed_rules = status_counts.get(RuleStatus.PASS, 0)
            compliance_percentage = (passed_rules / total_rules * 100) if total_rules > 0 else 0
            
            # Create scan session
            session_data = {
                "session_id": session_id,
                "hostname": first_result.hostname,
                "os_type": first_result.os_type,
                "os_version": first_result.os_version,
                "hardening_level": first_result.hardening_level,
                "category_filter": None,
                "is_dry_run": True,  # Default to dry run for migrated data
                "start_time": first_result.created_at,
                "end_time": first_result.created_at,  # Use same time as start
                "total_rules": total_rules,
                "passed_rules": status_counts.get(RuleStatus.PASS, 0),
                "failed_rules": status_counts.get(RuleStatus.FAIL, 0),
                "error_rules": status_counts.get(RuleStatus.ERROR, 0),
                "skipped_rules": status_counts.get(RuleStatus.SKIP, 0),
                "compliance_percentage": compliance_percentage,
                "execution_summary": {
                    "status_counts": status_counts,
                    "migrated_from_sqlite": True
                },
                "system_info_id": None,
                "results": [str(result.id) for result in results],
                "notes": "Migrated from SQLite database",
                "tags": ["migrated", "sqlite"],
                "created_at": first_result.created_at,
                "updated_at": first_result.created_at
            }
            
            session = ScanSession(**session_data)
            await self.mongodb_manager.create_scan_session(session)
            created_count += 1
        
        logger.info(f"Created {created_count} scan sessions")
        return created_count
    
    async def verify_migration(self) -> Dict[str, Any]:
        """Verify that migration was successful"""
        verification_results = {}
        
        try:
            # Count documents in MongoDB collections
            collections_to_check = [
                "hardening_results",
                "system_info", 
                "scan_sessions"
            ]
            
            for collection_name in collections_to_check:
                collection = self.mongodb_manager.get_collection(collection_name)
                count = await collection.count_documents({})
                verification_results[collection_name] = count
            
            # Check SQLite count for comparison
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM hardening_results")
            sqlite_count = cursor.fetchone()[0]
            conn.close()
            
            verification_results["sqlite_hardening_results"] = sqlite_count
            verification_results["migration_successful"] = (
                verification_results["hardening_results"] == sqlite_count
            )
            
            logger.info(f"Migration verification: {verification_results}")
            return verification_results
            
        except Exception as e:
            logger.error(f"Migration verification failed: {e}")
            return {"error": str(e)}

# CLI command for migration
async def run_migration(sqlite_db_path: str = "policy_guard.db"):
    """Run the migration process"""
    migrator = SQLiteToMongoDBMigrator(sqlite_db_path)
    
    print("Starting SQLite to MongoDB migration...")
    
    # Run migration
    results = await migrator.migrate_all_data()
    print(f"Migration completed: {results}")
    
    # Verify migration
    verification = await migrator.verify_migration()
    print(f"Migration verification: {verification}")
    
    # Close connections
    await migrator.mongodb_manager.close()
    
    return results, verification

if __name__ == "__main__":
    asyncio.run(run_migration())
