#!/usr/bin/env python3

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from orchestrator import MCPOrchestrator
from workflow_templates import WorkflowTemplateManager


@dataclass
class MCPRequest:
    jsonrpc: str
    id: Optional[str]
    method: str
    params: Optional[Dict[str, Any]] = None


@dataclass
class MCPResponse:
    jsonrpc: str
    id: Optional[str]
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class MCPWorkflowServer:
    def __init__(self):
        self.orchestrator = MCPOrchestrator()
        self.template_manager = WorkflowTemplateManager()
        self.logger = logging.getLogger(__name__)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    async def handle_request(self, request: MCPRequest) -> Optional[MCPResponse]:
        """Handle incoming MCP requests."""
        self.logger.info(f"Received request: method={request.method}, id={request.id}, params={request.params}")
        
        try:
            if request.method == "initialize":
                return await self.handle_initialize(request)
            elif request.method == "notifications/initialized":
                # This is a notification, no response required
                self.logger.info("Handled notifications/initialized")
                return None
            elif request.method == "tools/list":
                return await self.handle_tools_list(request)
            elif request.method == "tools/call":
                return await self.handle_tools_call(request)
            elif request.method == "resources/list":
                return await self.handle_resources_list(request)
            elif request.method == "resources/read":
                return await self.handle_resources_read(request)
            elif request.method == "prompts/list":
                return await self.handle_prompts_list(request)
            elif request.method.startswith("notifications/"):
                # Handle other notifications (no response required)
                self.logger.info(f"Handled notification: {request.method}")
                return None
            else:
                self.logger.error(f"Unknown method: {request.method}")
                return MCPResponse(
                    jsonrpc="2.0",
                    id=request.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {request.method}"
                    }
                )
        except Exception as e:
            self.logger.error(f"Error handling request: {e}", exc_info=True)
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            )
    
    async def handle_initialize(self, request: MCPRequest) -> MCPResponse:
        """Handle initialization request."""
        return MCPResponse(
            jsonrpc="2.0",
            id=request.id,
            result={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "serverInfo": {
                    "name": "mcpuppet",
                    "version": "1.0.0"
                }
            }
        )
    
    async def handle_tools_list(self, request: MCPRequest) -> MCPResponse:
        """List available tools."""
        tools = [
            {
                "name": "execute_workflow",
                "description": "Execute a workflow with the specified template and data",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "template_name": {
                            "type": "string",
                            "description": "Name of the workflow template to execute"
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Unique session identifier for the workflow"
                        },
                        "data": {
                            "type": "object",
                            "description": "Data to process through the workflow"
                        }
                    },
                    "required": ["template_name", "session_id", "data"]
                }
            },
            {
                "name": "call_tool",
                "description": "Call a specific tool with policy enforcement",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session identifier"
                        },
                        "tool_name": {
                            "type": "string",
                            "description": "Name of the tool to call"
                        },
                        "arguments": {
                            "type": "object",
                            "description": "Arguments to pass to the tool"
                        }
                    },
                    "required": ["session_id", "tool_name", "arguments"]
                }
            },
            {
                "name": "get_workflow_status",
                "description": "Get the status of a workflow session",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session identifier"
                        }
                    },
                    "required": ["session_id"]
                }
            },
            {
                "name": "list_templates",
                "description": "List available workflow templates",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_audit_report",
                "description": "Get comprehensive audit report for a session",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session identifier (optional)"
                        }
                    }
                }
            }
        ]
        
        return MCPResponse(
            jsonrpc="2.0",
            id=request.id,
            result={"tools": tools}
        )
    
    async def handle_tools_call(self, request: MCPRequest) -> MCPResponse:
        """Handle tool calls."""
        params = request.params or {}
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        self.logger.info(f"Tool call: name={tool_name}, arguments={arguments}")
        
        if tool_name == "execute_workflow":
            return await self.execute_workflow(request.id, arguments)
        elif tool_name == "call_tool":
            return await self.call_tool(request.id, arguments)
        elif tool_name == "get_workflow_status":
            return await self.get_workflow_status(request.id, arguments)
        elif tool_name == "list_templates":
            return await self.list_templates(request.id, arguments)
        elif tool_name == "get_audit_report":
            return await self.get_audit_report(request.id, arguments)
        else:
            self.logger.error(f"Unknown tool: {tool_name}")
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32602,
                    "message": f"Unknown tool: {tool_name}"
                }
            )
    
    async def execute_workflow(self, request_id: str, arguments: Dict[str, Any]) -> MCPResponse:
        """Execute a complete workflow."""
        try:
            template_name = arguments["template_name"]
            session_id = arguments["session_id"]
            data = arguments["data"]
            
            # Get workflow template
            template = self.template_manager.get_template(template_name)
            if not template:
                return MCPResponse(
                    jsonrpc="2.0",
                    id=request_id,
                    error={
                        "code": -32602,
                        "message": f"Template not found: {template_name}"
                    }
                )
            
            # Execute workflow steps
            results = []
            for step in template.steps:
                result = await self.orchestrator.call_tool(
                    session_id,
                    step.tool_name,
                    {"data": data}
                )
                results.append({
                    "tool": step.tool_name,
                    "success": result["success"],
                    "result": result.get("result"),
                    "error": result.get("error")
                })
                
                # Stop if step failed
                if not result["success"]:
                    break
            
            # Get final status
            session_status = self.orchestrator.get_session_status(session_id)
            
            # Format response
            success_count = sum(1 for r in results if r["success"])
            total_count = len(results)
            
            result_text = f"Workflow '{template_name}' executed for session {session_id}\n\n"
            result_text += f"Steps completed: {success_count}/{total_count}\n\n"
            
            for i, result in enumerate(results, 1):
                status = "✅" if result["success"] else "❌"
                result_text += f"{i}. {status} {result['tool']}\n"
                if result.get("error"):
                    result_text += f"   Error: {result['error']}\n"
            
            result_text += f"\nSession Status: {session_status.get('status', 'unknown')}"
            
            return MCPResponse(
                jsonrpc="2.0",
                id=request_id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            )
            
        except Exception as e:
            return MCPResponse(
                jsonrpc="2.0",
                id=request_id,
                error={
                    "code": -32603,
                    "message": f"Workflow execution failed: {str(e)}"
                }
            )
    
    async def call_tool(self, request_id: str, arguments: Dict[str, Any]) -> MCPResponse:
        """Call a specific tool."""
        try:
            session_id = arguments["session_id"]
            tool_name = arguments["tool_name"]
            tool_arguments = arguments["arguments"]
            
            result = await self.orchestrator.call_tool(session_id, tool_name, tool_arguments)
            
            # Format response
            status = "✅ Success" if result.get("success") else "❌ Failed"
            result_text = f"Tool '{tool_name}' called for session {session_id}\n\n"
            result_text += f"Status: {status}\n"
            
            if result.get("result"):
                result_text += f"Result: {result['result']}\n"
            if result.get("error"):
                result_text += f"Error: {result['error']}\n"
            
            return MCPResponse(
                jsonrpc="2.0",
                id=request_id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            )
            
        except Exception as e:
            return MCPResponse(
                jsonrpc="2.0",
                id=request_id,
                error={
                    "code": -32603,
                    "message": f"Tool call failed: {str(e)}"
                }
            )
    
    async def get_workflow_status(self, request_id: str, arguments: Dict[str, Any]) -> MCPResponse:
        """Get workflow status."""
        try:
            session_id = arguments["session_id"]
            status = self.orchestrator.get_session_status(session_id)
            
            # Format response
            result_text = f"Session {session_id} Status:\n\n"
            result_text += f"Status: {status.get('status', 'unknown')}\n"
            result_text += f"Tools called: {len(status.get('tools_called', []))}\n"
            
            if status.get('current_step'):
                result_text += f"Current step: {status['current_step']}\n"
            
            if status.get('tools_called'):
                result_text += "\nTools called:\n"
                for tool in status['tools_called']:
                    result_text += f"  • {tool}\n"
            
            return MCPResponse(
                jsonrpc="2.0",
                id=request_id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            )
            
        except Exception as e:
            return MCPResponse(
                jsonrpc="2.0",
                id=request_id,
                error={
                    "code": -32603,
                    "message": f"Status retrieval failed: {str(e)}"
                }
            )
    
    async def list_templates(self, request_id: str, arguments: Dict[str, Any]) -> MCPResponse:
        """List available workflow templates."""
        self.logger.info(f"list_templates called with arguments: {arguments}")
        
        try:
            templates = self.template_manager.list_templates()
            self.logger.info(f"Retrieved {len(templates)} templates: {[t.get('name', 'unnamed') for t in templates]}")
            
            # Format templates for display
            template_list = []
            for template in templates:
                template_list.append(f"• {template.get('name', 'unnamed')}: {template.get('description', 'No description')}")
            
            result = {
                "content": [
                    {
                        "type": "text",
                        "text": f"Available workflow templates:\n\n" + "\n".join(template_list)
                    }
                ]
            }
            self.logger.info(f"Returning result: {result}")
            
            return MCPResponse(
                jsonrpc="2.0",
                id=request_id,
                result=result
            )
            
        except Exception as e:
            self.logger.error(f"Template listing failed: {e}", exc_info=True)
            return MCPResponse(
                jsonrpc="2.0",
                id=request_id,
                error={
                    "code": -32603,
                    "message": f"Template listing failed: {str(e)}"
                }
            )
    
    async def get_audit_report(self, request_id: str, arguments: Dict[str, Any]) -> MCPResponse:
        """Get audit report."""
        try:
            session_id = arguments.get("session_id")
            report = self.orchestrator.audit_monitor.generate_compliance_report(session_id)
            
            # Format response
            result_text = f"Audit Report" + (f" for session {session_id}" if session_id else "") + "\n\n"
            result_text += f"Total sessions: {report.get('total_sessions', 0)}\n"
            result_text += f"Policy violations: {report.get('policy_violations', 0)}\n"
            result_text += f"Success rate: {report.get('success_rate', 0):.1%}\n"
            
            if report.get('violations'):
                result_text += "\nViolations:\n"
                for violation in report['violations']:
                    result_text += f"  • {violation}\n"
            
            return MCPResponse(
                jsonrpc="2.0",
                id=request_id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            )
            
        except Exception as e:
            return MCPResponse(
                jsonrpc="2.0",
                id=request_id,
                error={
                    "code": -32603,
                    "message": f"Audit report generation failed: {str(e)}"
                }
            )
    
    async def handle_resources_list(self, request: MCPRequest) -> MCPResponse:
        """List available resources."""
        resources = [
            {
                "uri": "workflow://templates",
                "name": "Workflow Templates",
                "description": "Available workflow templates",
                "mimeType": "application/json"
            },
            {
                "uri": "workflow://config",
                "name": "Configuration",
                "description": "Current system configuration",
                "mimeType": "application/json"
            }
        ]
        
        return MCPResponse(
            jsonrpc="2.0",
            id=request.id,
            result={"resources": resources}
        )
    
    async def handle_resources_read(self, request: MCPRequest) -> MCPResponse:
        """Read resource content."""
        params = request.params or {}
        uri = params.get("uri")
        
        if uri == "workflow://templates":
            templates = self.template_manager.list_templates()
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                result={
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(templates, indent=2)
                        }
                    ]
                }
            )
        elif uri == "workflow://config":
            config = self.orchestrator.config
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                result={
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(config, indent=2)
                        }
                    ]
                }
            )
        else:
            return MCPResponse(
                jsonrpc="2.0",
                id=request.id,
                error={
                    "code": -32602,
                    "message": f"Resource not found: {uri}"
                }
            )
    
    async def handle_prompts_list(self, request: MCPRequest) -> MCPResponse:
        """Handle prompts list request."""
        # Return empty prompts list - this server doesn't provide prompts
        return MCPResponse(
            jsonrpc="2.0",
            id=request.id,
            result={"prompts": []}
        )
    
    async def run(self):
        """Run the MCP server."""
        self.logger.info("Starting MCPuppet Server")
        
        # Read from stdin and write to stdout for MCP transport
        while True:
            try:
                # Read JSON-RPC message from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                # Parse request
                try:
                    request_data = json.loads(line.strip())
                    request = MCPRequest(
                        jsonrpc=request_data["jsonrpc"],
                        id=request_data.get("id"),
                        method=request_data["method"],
                        params=request_data.get("params")
                    )
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON: {e}")
                    continue
                except KeyError as e:
                    self.logger.error(f"Missing required field: {e}")
                    continue
                
                # Handle request
                response = await self.handle_request(request)
                
                # Send response (only if not None - notifications don't get responses)
                if response is not None:
                    response_data = {
                        "jsonrpc": response.jsonrpc,
                        "id": response.id
                    }
                    
                    if response.result is not None:
                        response_data["result"] = response.result
                    if response.error is not None:
                        response_data["error"] = response.error
                    
                    self.logger.info(f"Sending response: {response_data}")
                    print(json.dumps(response_data))
                    sys.stdout.flush()
                
            except Exception as e:
                self.logger.error(f"Server error: {e}")
                break
        
        self.logger.info("MCPuppet Server stopped")


async def main():
    """Main entry point for MCP server."""
    # Change to the script's directory to ensure relative paths work
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    server = MCPWorkflowServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())