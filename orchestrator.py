import asyncio
import json
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import httpx
from pydantic import BaseModel

from audit_monitor import AuditMonitor
from workflow_policies import WorkflowPolicyEngine


class ToolCallStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ToolCall:
    id: str
    tool_name: str
    arguments: Dict[str, Any]
    timestamp: datetime
    status: ToolCallStatus
    result: Optional[Any] = None
    error: Optional[str] = None


class WorkflowSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.tool_calls: List[ToolCall] = []
        self.state: Dict[str, Any] = {}
        self.start_time = datetime.now()
        self.active_workflow: Optional[str] = None
    
    def add_tool_call(self, tool_call: ToolCall):
        self.tool_calls.append(tool_call)
    
    def get_completed_tools(self) -> List[str]:
        return [
            call.tool_name for call in self.tool_calls 
            if call.status == ToolCallStatus.COMPLETED
        ]
    
    def get_failed_tools(self) -> List[str]:
        return [
            call.tool_name for call in self.tool_calls 
            if call.status == ToolCallStatus.FAILED
        ]


class MCPOrchestrator:
    def __init__(self, config_path: str = "config.json"):
        self.logger = logging.getLogger(__name__)
        # Make config path absolute relative to this file's directory
        if not os.path.isabs(config_path):
            config_path = os.path.join(os.path.dirname(__file__), config_path)
        self.config = self._load_config(config_path)
        self.audit_monitor = AuditMonitor()
        self.policy_engine = WorkflowPolicyEngine(self.config)
        self.sessions: Dict[str, WorkflowSession] = {}
        self.downstream_servers: Dict[str, str] = self.config.get("downstream_servers", {})
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config file {config_path} not found, using defaults")
            return {
                "downstream_servers": {
                    "validate_data": "http://localhost:8001",
                    "process_data": "http://localhost:8002", 
                    "backup_data": "http://localhost:8003",
                    "send_notification": "http://localhost:8004",
                    "require_approval": "http://localhost:8005"
                },
                "policies": {}
            }
    
    def create_session(self, session_id: str) -> WorkflowSession:
        session = WorkflowSession(session_id)
        self.sessions[session_id] = session
        self.audit_monitor.log_session_start(session_id)
        return session
    
    def get_session(self, session_id: str) -> Optional[WorkflowSession]:
        return self.sessions.get(session_id)
    
    async def call_tool(self, session_id: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)
        
        tool_call = ToolCall(
            id=f"{session_id}_{len(session.tool_calls)}",
            tool_name=tool_name,
            arguments=arguments,
            timestamp=datetime.now(),
            status=ToolCallStatus.PENDING
        )
        
        session.add_tool_call(tool_call)
        
        # Log the attempt
        self.audit_monitor.log_tool_call_attempt(session_id, tool_name, arguments)
        
        try:
            # Check policy enforcement
            policy_result = self.policy_engine.can_execute_tool(
                tool_name, session.get_completed_tools(), session.state
            )
            
            if not policy_result.allowed:
                tool_call.status = ToolCallStatus.BLOCKED
                tool_call.error = policy_result.reason
                self.audit_monitor.log_policy_violation(
                    session_id, tool_name, policy_result.reason
                )
                return {
                    "success": False,
                    "error": f"Policy violation: {policy_result.reason}",
                    "tool_call_id": tool_call.id
                }
            
            # Check if manual approval is required
            if policy_result.requires_approval:
                tool_call.status = ToolCallStatus.APPROVED
                approval_result = await self._request_approval(session_id, tool_name, arguments)
                if not approval_result:
                    tool_call.status = ToolCallStatus.BLOCKED
                    tool_call.error = "Manual approval denied"
                    return {
                        "success": False,
                        "error": "Manual approval required and denied",
                        "tool_call_id": tool_call.id
                    }
            
            # Execute the tool call
            result = await self._execute_downstream_tool(tool_name, arguments)
            
            tool_call.status = ToolCallStatus.COMPLETED
            tool_call.result = result
            
            # Update session state
            session.state[f"{tool_name}_result"] = result
            
            self.audit_monitor.log_tool_call_completion(
                session_id, tool_name, result, success=True
            )
            
            return {
                "success": True,
                "result": result,
                "tool_call_id": tool_call.id
            }
            
        except Exception as e:
            tool_call.status = ToolCallStatus.FAILED
            tool_call.error = str(e)
            
            self.audit_monitor.log_tool_call_completion(
                session_id, tool_name, None, success=False, error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "tool_call_id": tool_call.id
            }
    
    async def _execute_downstream_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        server_url = self.downstream_servers.get(tool_name)
        if not server_url:
            raise ValueError(f"No downstream server configured for tool: {tool_name}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{server_url}/call_tool",
                    json={"tool_name": tool_name, "arguments": arguments},
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                # Downstream server failure - raise the error to be properly recorded
                self.logger.error(f"Downstream server {server_url} failed: {e}")
                raise ConnectionError(f"Downstream server {server_url} is not available: {e}")
            except httpx.HTTPStatusError as e:
                # HTTP error response from server
                self.logger.error(f"Downstream server {server_url} returned error {e.response.status_code}: {e.response.text}")
                raise RuntimeError(f"Downstream server {server_url} returned error {e.response.status_code}: {e.response.text}")
    
    
    async def _request_approval(self, session_id: str, tool_name: str, arguments: Dict[str, Any]) -> bool:
        # For demo purposes, simulate approval request
        self.audit_monitor.log_approval_request(session_id, tool_name, arguments)
        
        # In a real implementation, this would integrate with an approval system
        # For now, we'll simulate approval for demo purposes
        print(f"⚠️  Manual approval required for {tool_name}")
        print(f"   Session: {session_id}")
        print(f"   Arguments: {arguments}")
        print("   Auto-approving for demo...")
        
        return True
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        completed_tools = session.get_completed_tools()
        failed_tools = session.get_failed_tools()
        
        return {
            "session_id": session_id,
            "start_time": session.start_time.isoformat(),
            "active_workflow": session.active_workflow,
            "total_calls": len(session.tool_calls),
            "completed_tools": completed_tools,
            "failed_tools": failed_tools,
            "current_state": session.state
        }
    
    def get_all_sessions_status(self) -> List[Dict[str, Any]]:
        return [self.get_session_status(sid) for sid in self.sessions.keys()]