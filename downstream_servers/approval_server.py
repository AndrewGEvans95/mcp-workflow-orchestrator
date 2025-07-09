import asyncio
import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]


class ToolCallResponse(BaseModel):
    success: bool
    result: Any
    error: str = None


app = FastAPI(title="Approval MCP Server", version="1.0.0")
logger = logging.getLogger(__name__)

# In-memory store for approval requests (in production, use a database)
approval_requests = {}


@app.post("/call_tool", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    if request.tool_name != "require_approval":
        raise HTTPException(status_code=400, detail=f"Unknown tool: {request.tool_name}")
    
    try:
        result = await require_approval(request.arguments)
        return ToolCallResponse(success=True, result=result)
    except Exception as e:
        logger.error(f"Error in require_approval: {str(e)}")
        return ToolCallResponse(success=False, error=str(e))


async def require_approval(arguments: Dict[str, Any]) -> Dict[str, Any]:
    # Simulate approval process
    approval_type = arguments.get("approval_type", "manual")
    approval_level = arguments.get("approval_level", "standard")
    requested_action = arguments.get("requested_action", "unknown")
    justification = arguments.get("justification", "")
    
    # Simulate approval delay
    await asyncio.sleep(0.3)
    
    approval_timestamp = datetime.now()
    approval_id = f"approval_{approval_timestamp.strftime('%Y%m%d_%H%M%S')}_{id(requested_action) % 10000}"
    
    # Create approval request
    approval_request = {
        "approval_id": approval_id,
        "created_at": approval_timestamp.isoformat(),
        "requested_action": requested_action,
        "approval_type": approval_type,
        "approval_level": approval_level,
        "justification": justification,
        "status": "pending",
        "expires_at": (approval_timestamp + timedelta(hours=24)).isoformat(),
        "metadata": arguments.get("metadata", {})
    }
    
    # Determine approval workflow based on level
    approval_workflow = {}
    
    if approval_level == "standard":
        approval_workflow = {
            "required_approvers": 1,
            "approval_hierarchy": ["manager"],
            "timeout_hours": 24,
            "escalation_enabled": True,
            "escalation_after_hours": 8
        }
    elif approval_level == "elevated":
        approval_workflow = {
            "required_approvers": 2,
            "approval_hierarchy": ["manager", "director"],
            "timeout_hours": 48,
            "escalation_enabled": True,
            "escalation_after_hours": 4
        }
    elif approval_level == "critical":
        approval_workflow = {
            "required_approvers": 3,
            "approval_hierarchy": ["manager", "director", "ciso"],
            "timeout_hours": 72,
            "escalation_enabled": True,
            "escalation_after_hours": 2
        }
    
    # Auto-approve certain types for demo purposes
    auto_approve_types = arguments.get("auto_approve_types", ["standard_processing"])
    
    if approval_type == "automatic" or requested_action in auto_approve_types:
        approval_decision = {
            "approved": True,
            "approved_by": "system",
            "approved_at": approval_timestamp.isoformat(),
            "approval_method": "automatic",
            "approval_reason": "Matches auto-approval criteria"
        }
        approval_request["status"] = "approved"
    else:
        # For demo purposes, simulate manual approval
        # In production, this would integrate with an approval system
        approval_decision = {
            "approved": True,  # Auto-approve for demo
            "approved_by": "demo_approver",
            "approved_at": approval_timestamp.isoformat(),
            "approval_method": "manual",
            "approval_reason": "Demo auto-approval"
        }
        approval_request["status"] = "approved"
    
    # Store approval request
    approval_requests[approval_id] = approval_request
    
    # Add audit trail
    audit_trail = [
        {
            "timestamp": approval_timestamp.isoformat(),
            "action": "approval_requested",
            "actor": "system",
            "details": f"Approval requested for {requested_action}"
        },
        {
            "timestamp": approval_timestamp.isoformat(),
            "action": "approval_granted",
            "actor": approval_decision["approved_by"],
            "details": approval_decision["approval_reason"]
        }
    ]
    
    # Check for approval errors (simulate occasional failures)
    if arguments.get("simulate_failure", False):
        raise Exception("Simulated approval failure - approval service unavailable")
    
    # Add compliance tracking
    compliance_tracking = {
        "compliance_framework": arguments.get("compliance_framework", "SOX"),
        "risk_level": arguments.get("risk_level", "medium"),
        "segregation_of_duties": True,
        "approval_documented": True,
        "audit_log_retained": True,
        "retention_period_days": 2555  # 7 years
    }
    
    # Add notification info
    notification_info = {
        "approvers_notified": ["manager@company.com"],
        "notification_sent_at": approval_timestamp.isoformat(),
        "reminder_schedule": ["4h", "8h", "24h"],
        "escalation_contacts": ["director@company.com"]
    }
    
    return {
        "success": True,
        "approval_id": approval_id,
        "approved": approval_decision["approved"],
        "approval_request": approval_request,
        "approval_decision": approval_decision,
        "approval_workflow": approval_workflow,
        "audit_trail": audit_trail,
        "compliance_tracking": compliance_tracking,
        "notification_info": notification_info,
        "message": f"Approval {'granted' if approval_decision['approved'] else 'denied'} for {requested_action}"
    }


@app.get("/approval/{approval_id}")
async def get_approval_status(approval_id: str):
    if approval_id not in approval_requests:
        raise HTTPException(status_code=404, detail="Approval request not found")
    
    return approval_requests[approval_id]


@app.get("/approvals")
async def list_approvals():
    return list(approval_requests.values())


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "approval_server"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)