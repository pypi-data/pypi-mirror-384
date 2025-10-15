"""
FastAPI Application for OS Forge

Main API endpoints and application setup.
"""

import json
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from .config import Config
from security.auth import verify_api_key
from database.manager import db_manager, get_db
from database.mongodb_schemas import HardeningResult
from reporting.generator import ReportGenerator
from agents.linux.linux_agent import LinuxAgent
from agents.windows.windows_agent import WindowsAgent
from agents.macos.macos_agent import MacOSAgent
from agents.common.os_detector import OSDetector
from agents.common.base_agent import RuleStatus
from agents.linux.linux_rules import LinuxRuleCategory, get_linux_hardening_rules
from agents.windows.windows_rules import WindowsRuleCategory, get_windows_hardening_rules
from agents.macos.macos_rules import MacOSRuleCategory, get_macos_hardening_rules
import platform


# Initialize components
os_detector = OSDetector()
current_os = os_detector.detect_os()

# Initialize appropriate agent based on OS
if current_os['type'] == "linux":
    policy_engine = LinuxAgent()
    rules_module = get_linux_hardening_rules
elif current_os['type'] == "windows":
    policy_engine = WindowsAgent()
    rules_module = get_windows_hardening_rules
elif current_os['type'] == "macos":
    policy_engine = MacOSAgent()
    rules_module = get_macos_hardening_rules
else:
    # Fallback to Linux agent for unknown OS
    policy_engine = LinuxAgent()
    rules_module = get_linux_hardening_rules

report_generator = ReportGenerator()

# Create FastAPI app
app = FastAPI(
    title=Config.API_TITLE,
    description=Config.API_DESCRIPTION,
    version=Config.API_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        await db_manager.initialize()
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
        print("Database features will be disabled. Set MONGODB_URI environment variable to enable.")


@app.get("/")
async def read_root():
    """
    Get system information and API status
    
    Returns basic information about the system and available rules.
    """
    try:
        await db_manager.initialize()
        database_status = "MongoDB"
    except Exception:
        database_status = "Disabled (MongoDB URI not set)"
    
    rules = rules_module()
    return {
        "message": "OS Forge - Multi-Platform System Hardening Tool",
        "detected_os": current_os['type'],
        "os_distribution": current_os.get('distribution', {}).get('name', 'Unknown'),
        "available_rules": len(rules),
        "agent_type": type(policy_engine).__name__,
        "rule_categories": list(set(rule.get("category", "unknown") for rule in rules)),
        "database": database_status
    }


@app.get("/rules")
def get_rules(level: Optional[str] = None, category: Optional[str] = None):
    """
    Get applicable hardening rules
    
    Args:
        level: Hardening level (basic, moderate, strict) - if None, returns all rules
        category: Optional category filter
        
    Returns:
        Dict containing applicable rules and count
    """
    rules = rules_module()
    
    # Filter by level (only if specified)
    if level:
        rules = [rule for rule in rules if level in rule.get("level", [])]
    
    # Filter by category
    if category:
        rules = [rule for rule in rules if rule.get("category") == category]
    
    return {"rules": rules, "count": len(rules)}


@app.post("/run")
async def run_hardening(level: Optional[str] = None, dry_run: bool = True, category: Optional[str] = None, api_key: str = Depends(verify_api_key)):
    """
    Execute hardening rules
    
    This endpoint requires authentication and executes security hardening rules.
    
    Args:
        level: Hardening level (basic, moderate, strict) - if None, executes all rules
        dry_run: If True, only check current state without applying changes
        category: Optional category filter
        api_key: Valid API key (provided via Authorization header)
        
    Returns:
        Dict containing execution results and summary
    """
    # Get rules based on filters
    rules = rules_module()
    
    # Filter by level
    if level:
        rules = [rule for rule in rules if level in rule.get("level", [])]
    
    # Filter by category
    if category:
        rules = [rule for rule in rules if rule.get("category") == category]
    
    results = []
    
    # Initialize database (if available)
    try:
        await db_manager.initialize()
        database_available = True
    except Exception:
        database_available = False
    
    # Create scan session (if database available)
    session_id = None
    if database_available:
        import uuid
        from datetime import datetime
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "hostname": platform.node(),
            "os_type": current_os['type'],
            "os_version": current_os.get('version', 'unknown'),
            "hardening_level": level or "all",
            "category_filter": category,
            "is_dry_run": dry_run,
            "start_time": datetime.utcnow(),
            "total_rules": len(rules),
            "passed_rules": 0,
            "failed_rules": 0,
            "error_rules": 0,
            "skipped_rules": 0,
            "compliance_percentage": 0,
            "execution_summary": {},
            "system_info_id": None,
            "results": [],
            "notes": f"API execution - Level: {level}, Dry Run: {dry_run}",
            "tags": ["api", "execution"],
            "status": "running"
        }
        await db_manager.create_scan_session(session_data)
    
    for rule in rules:
        try:
            # Check rule first
            check_result = policy_engine.check_rule(rule)
            
            # If dry run, just return the check result
            if dry_run:
                result = {
                    "rule_id": check_result.rule_id,
                    "description": check_result.description,
                    "severity": rule["severity"],
                    "status": check_result.status.value,
                    "old_value": check_result.old_value,
                    "new_value": check_result.new_value,
                    "error": check_result.error
                }
            else:
                # Apply remediation if not dry run and rule failed
                if check_result.status == RuleStatus.FAIL:
                    remediate_result = policy_engine.remediate_rule(rule, dry_run=False)
                    result = {
                        "rule_id": remediate_result.rule_id,
                        "description": remediate_result.description,
                        "severity": rule["severity"],
                        "status": remediate_result.status.value,
                        "old_value": remediate_result.old_value,
                        "new_value": remediate_result.new_value,
                        "error": remediate_result.error
                    }
                else:
                    # Rule already passes, return check result
                    result = {
                        "rule_id": check_result.rule_id,
                        "description": check_result.description,
                        "severity": rule["severity"],
                        "status": check_result.status.value,
                        "old_value": check_result.old_value,
                        "new_value": check_result.new_value,
                        "error": check_result.error
                    }
            
            results.append(result)
            
            # Save to MongoDB
            result_data = {
                "rule_id": result["rule_id"],
                "rule_name": result["description"],
                "rule_category": rule.get("category", "unknown"),
                "hostname": platform.node(),
                "os_type": current_os['type'],
                "os_version": current_os.get('version', 'unknown'),
                "hardening_level": level or "all",
                "status": result["status"],
                "severity": result["severity"],
                "old_value": result.get("old_value"),
                "new_value": result.get("new_value"),
                "expected_value": rule.get("expected"),
                "error_message": result.get("error"),
                "execution_time": None,
                "check_output": None,
                "remediate_output": None,
                "rollback_data": {"rollback_command": rule.get("rollback", ""), "original_value": result.get("old_value")},
                "is_remediated": not dry_run and result["status"] == "pass",
                "is_rollback_available": bool(rule.get("rollback")),
                "compliance_score": None,
                "scan_session_id": session_id
            }
            # Store result in database (if available)
            if database_available:
                await db_manager.create_hardening_result(result_data)
            
        except Exception as e:
            # Handle rule execution errors
            error_result = {
                "rule_id": rule["id"],
                "description": rule["description"],
                "severity": rule["severity"],
                "status": "error",
                "error": str(e)
            }
            results.append(error_result)
    
    # Update scan session with final results (if database available)
    if database_available and session_id:
        passed_count = sum(1 for r in results if r["status"] == "pass")
        failed_count = sum(1 for r in results if r["status"] == "fail")
        error_count = sum(1 for r in results if r["status"] == "error")
        compliance_percentage = (passed_count / len(results) * 100) if results else 0
        
        session_updates = {
            "end_time": datetime.utcnow(),
            "passed_rules": passed_count,
            "failed_rules": failed_count,
            "error_rules": error_count,
            "compliance_percentage": compliance_percentage,
            "execution_summary": {
                "total_rules": len(results),
                "passed": passed_count,
                "failed": failed_count,
                "errors": error_count,
                "compliance_percentage": compliance_percentage
            },
            "status": "completed"
        }
        await db_manager.update_scan_session(session_id, session_updates)
    
    return {
        "status": "completed",
        "dry_run": dry_run,
        "level": level,
        "category": category,
        "session_id": session_id,
        "results": results,
        "summary": {
            "total": len(results),
            "passed": passed_count,
            "failed": failed_count,
            "errors": error_count,
            "compliance_percentage": compliance_percentage
        }
    }


@app.get("/history")
async def get_history():
    """
    Get hardening execution history
    
    Returns the latest 50 execution results.
    """
    await db_manager.initialize()
    results = await db_manager.get_hardening_results(platform.node(), 50)
    
    return {
        "hostname": platform.node(),
        "total_results": len(results),
        "history": [
            {
                "id": result.get("id"),
                "rule_id": result.get("rule_id"),
                "description": result.get("rule_name"),
                "status": result.get("status"),
                "timestamp": result.get("created_at")
            } for result in results
        ]
    }


@app.get("/report", response_class=HTMLResponse)
def generate_report():
    """
    Generate HTML compliance report
    
    Returns an HTML page with detailed compliance information.
    """
    try:
        db = next(get_db())
        results = db.query(HardeningResult).order_by(HardeningResult.timestamp.desc()).limit(100).all()
        
        # Convert ORM objects to dictionaries for report generator
        formatted_results = []
        for result in results:
            formatted_results.append({
                "rule_id": result.rule_id or "unknown",
                "description": result.rule_name or "Unknown",
                "severity": result.severity or "medium",
                "status": result.status or "unknown",
                "old_value": result.old_value,
                "new_value": result.new_value,
                "timestamp": result.created_at or "unknown"
            })
        
        os_info = f"{current_os['type']} - {current_os.get('distribution', {}).get('name', 'Unknown')}"
        return report_generator.generate_html_report(formatted_results, os_info)
    except Exception as e:
        return f"<html><body><h1>Error generating report</h1><p>{str(e)}</p></body></html>"


@app.get("/report/pdf")
def generate_pdf_report():
    """
    Generate PDF compliance report
    
    Returns a downloadable PDF report with compliance information.
    """
    try:
        db = next(get_db())
        results = db.query(HardeningResult).order_by(HardeningResult.timestamp.desc()).limit(100).all()
        
        # Convert ORM objects to dictionaries for report generator
        formatted_results = []
        for result in results:
            formatted_results.append({
                "rule_id": result.rule_id or "unknown",
                "description": result.rule_name or "Unknown",
                "severity": result.severity or "medium",
                "status": result.status or "unknown",
                "old_value": result.old_value,
                "new_value": result.new_value,
                "timestamp": result.created_at or "unknown"
            })
        
        os_info = f"{current_os['type']} - {current_os.get('distribution', {}).get('name', 'Unknown')}"
        pdf_buffer = report_generator.generate_pdf_report(formatted_results, os_info)
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=os_forge_report.pdf"}
        )
    except Exception as e:
        return HTTPException(status_code=500, detail=f"Error generating PDF report: {str(e)}")


@app.post("/rollback/{rule_id}")
def rollback_rule(rule_id: str, api_key: str = Depends(verify_api_key)):
    """
    Rollback a specific hardening rule
    
    This endpoint requires authentication and reverts a previously applied rule.
    
    Args:
        rule_id: ID of the rule to rollback
        api_key: Valid API key (provided via Authorization header)
        
    Returns:
        Dict containing rollback results
    """
    db = next(get_db())
    
    # Find the latest result for this rule
    latest_result = db.query(HardeningResult).filter(
        HardeningResult.rule_id == rule_id
    ).order_by(HardeningResult.timestamp.desc()).first()
    
    if not latest_result:
        raise HTTPException(status_code=404, detail=f"No results found for rule {rule_id}")
    
    if not latest_result.rollback_data:
        raise HTTPException(status_code=400, detail=f"No rollback data available for rule {rule_id}")
    
    try:
        # Find the rule definition for rollback
        rules = rules_module()
        rule_def = None
        for rule in rules:
            if rule["id"] == rule_id:
                rule_def = rule
                break
        
        if not rule_def:
            raise HTTPException(status_code=404, detail=f"Rule definition not found for {rule_id}")
        
        # Execute rollback using agent
        rollback_data = json.loads(latest_result.rollback_data) if latest_result.rollback_data else {}
        rollback_result = policy_engine.rollback_rule(rule_def, rollback_data)
        
        if rollback_result.status == RuleStatus.PASS:
            # Log the rollback
            rollback_log = HardeningResult(
                rule_id=rule_id,
                description=f"ROLLBACK: {latest_result.description}",
                severity=latest_result.severity,
                status="rollback_success",
                old_value=latest_result.new_value,
                new_value=latest_result.old_value,
                rollback_data=json.dumps("")  # Clear rollback data after use
            )
            db.add(rollback_log)
            db.commit()
        
        return {
            "status": "success" if rollback_result.status == RuleStatus.PASS else "error",
            "message": f"Rollback {'successful' if rollback_result.status == RuleStatus.PASS else 'failed'} for rule {rule_id}",
            "rule_id": rule_id,
            "rollback_output": rollback_result.new_value,
            "error": rollback_result.error
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rollback/available")
async def get_rollback_options():
    """
    Get list of rules that can be rolled back
    
    Returns rules that have been applied and can be reverted.
    """
    try:
        # For now, return empty list since we don't have hardening results yet
        # This will be populated when users run hardening operations
        return {"rollback_options": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports")
async def get_reports():
    """
    Get list of available reports
    
    Returns a list of generated reports with metadata.
    """
    try:
        # For now, return empty list since we don't have reports yet
        # This will be populated when users generate reports
        return {"reports": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

