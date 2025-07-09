from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class WorkflowStepType(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    APPROVAL_GATE = "approval_gate"


@dataclass
class WorkflowStep:
    tool_name: str
    step_type: WorkflowStepType
    dependencies: List[str]
    conditions: Dict[str, Any]
    approval_required: bool = False
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    
    def can_execute(self, completed_tools: List[str], failed_tools: List[str], 
                   session_state: Dict[str, Any]) -> bool:
        # Check if all dependencies are completed
        for dep in self.dependencies:
            if dep not in completed_tools:
                return False
        
        # Check if any dependencies failed (unless specifically allowed)
        if not self.conditions.get("allow_failed_dependencies", False):
            for dep in self.dependencies:
                if dep in failed_tools:
                    return False
        
        # Check conditional execution
        if self.conditions:
            return self._evaluate_conditions(session_state)
        
        return True
    
    def _evaluate_conditions(self, session_state: Dict[str, Any]) -> bool:
        if "required_state" in self.conditions:
            required_state = self.conditions["required_state"]
            for key, expected_value in required_state.items():
                if session_state.get(key) != expected_value:
                    return False
        
        if "required_results" in self.conditions:
            required_results = self.conditions["required_results"]
            for tool_name, expected_result in required_results.items():
                result_key = f"{tool_name}_result"
                if result_key not in session_state:
                    return False
                
                actual_result = session_state[result_key]
                if not self._check_result_condition(actual_result, expected_result):
                    return False
        
        return True
    
    def _check_result_condition(self, actual_result: Any, expected_condition: Any) -> bool:
        if isinstance(expected_condition, dict):
            if "contains" in expected_condition:
                if isinstance(actual_result, dict):
                    return expected_condition["contains"] in actual_result
                elif isinstance(actual_result, str):
                    return expected_condition["contains"] in actual_result
            
            if "equals" in expected_condition:
                return actual_result == expected_condition["equals"]
            
            if "success" in expected_condition:
                if isinstance(actual_result, dict):
                    return actual_result.get("success", False) == expected_condition["success"]
        
        return actual_result == expected_condition


class WorkflowTemplate:
    def __init__(self, name: str, description: str, steps: List[Dict[str, Any]]):
        self.name = name
        self.description = description
        self.steps = [self._create_step(step_config) for step_config in steps]
        self.metadata = {}
    
    def _create_step(self, step_config: Dict[str, Any]) -> WorkflowStep:
        return WorkflowStep(
            tool_name=step_config["tool_name"],
            step_type=WorkflowStepType(step_config.get("step_type", "sequential")),
            dependencies=step_config.get("dependencies", []),
            conditions=step_config.get("conditions", {}),
            approval_required=step_config.get("approval_required", False),
            timeout_seconds=step_config.get("timeout_seconds"),
            retry_count=step_config.get("retry_count", 0)
        )
    
    def get_next_executable_steps(self, completed_tools: List[str], failed_tools: List[str], 
                                 session_state: Dict[str, Any]) -> List[WorkflowStep]:
        executable_steps = []
        
        for step in self.steps:
            if step.tool_name not in completed_tools and step.tool_name not in failed_tools:
                if step.can_execute(completed_tools, failed_tools, session_state):
                    executable_steps.append(step)
        
        return executable_steps
    
    def get_progress(self, completed_tools: List[str], failed_tools: List[str]) -> Dict[str, Any]:
        total_steps = len(self.steps)
        completed_steps = len([step for step in self.steps if step.tool_name in completed_tools])
        failed_steps = len([step for step in self.steps if step.tool_name in failed_tools])
        
        return {
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "remaining_steps": total_steps - completed_steps - failed_steps,
            "progress_percent": (completed_steps / total_steps * 100) if total_steps > 0 else 0,
            "is_complete": completed_steps == total_steps,
            "has_failures": failed_steps > 0
        }
    
    def is_complete(self, completed_tools: List[str]) -> bool:
        return all(step.tool_name in completed_tools for step in self.steps)
    
    def get_step_by_tool_name(self, tool_name: str) -> Optional[WorkflowStep]:
        for step in self.steps:
            if step.tool_name == tool_name:
                return step
        return None


class WorkflowTemplateManager:
    def __init__(self):
        self.templates: Dict[str, WorkflowTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        # Customer Onboarding Workflow
        customer_onboarding = WorkflowTemplate(
            name="customer_onboarding",
            description="Complete customer onboarding process with validation, processing, backup, and notification",
            steps=[
                {
                    "tool_name": "validate_data",
                    "step_type": "sequential",
                    "dependencies": [],
                    "conditions": {}
                },
                {
                    "tool_name": "process_data",
                    "step_type": "sequential",
                    "dependencies": ["validate_data"],
                    "conditions": {
                        "required_results": {
                            "validate_data": {"success": True}
                        }
                    }
                },
                {
                    "tool_name": "backup_data",
                    "step_type": "sequential",
                    "dependencies": ["process_data"],
                    "conditions": {
                        "required_results": {
                            "process_data": {"success": True}
                        }
                    }
                },
                {
                    "tool_name": "send_notification",
                    "step_type": "sequential",
                    "dependencies": ["backup_data"],
                    "conditions": {}
                }
            ]
        )
        
        # Financial Processing Workflow
        financial_processing = WorkflowTemplate(
            name="financial_processing",
            description="Secure financial processing with fraud check, approval, and audit trail",
            steps=[
                {
                    "tool_name": "validate_data",
                    "step_type": "sequential",
                    "dependencies": [],
                    "conditions": {}
                },
                {
                    "tool_name": "require_approval",
                    "step_type": "approval_gate",
                    "dependencies": ["validate_data"],
                    "conditions": {
                        "required_results": {
                            "validate_data": {"success": True}
                        }
                    },
                    "approval_required": True
                },
                {
                    "tool_name": "process_data",
                    "step_type": "sequential",
                    "dependencies": ["require_approval"],
                    "conditions": {
                        "required_results": {
                            "require_approval": {"approved": True}
                        }
                    }
                },
                {
                    "tool_name": "backup_data",
                    "step_type": "parallel",
                    "dependencies": ["process_data"],
                    "conditions": {}
                },
                {
                    "tool_name": "send_notification",
                    "step_type": "parallel",
                    "dependencies": ["process_data"],
                    "conditions": {}
                }
            ]
        )
        
        # Data Pipeline Workflow
        data_pipeline = WorkflowTemplate(
            name="data_pipeline",
            description="ETL data pipeline with validation, processing, and monitoring",
            steps=[
                {
                    "tool_name": "validate_data",
                    "step_type": "sequential",
                    "dependencies": [],
                    "conditions": {},
                    "timeout_seconds": 60
                },
                {
                    "tool_name": "process_data",
                    "step_type": "sequential",
                    "dependencies": ["validate_data"],
                    "conditions": {
                        "required_results": {
                            "validate_data": {"valid": True}
                        }
                    },
                    "timeout_seconds": 300
                },
                {
                    "tool_name": "backup_data",
                    "step_type": "sequential",
                    "dependencies": ["process_data"],
                    "conditions": {},
                    "timeout_seconds": 120
                }
            ]
        )
        
        # Emergency Response Workflow
        emergency_response = WorkflowTemplate(
            name="emergency_response",
            description="Emergency response workflow with immediate notification and approval bypass",
            steps=[
                {
                    "tool_name": "send_notification",
                    "step_type": "sequential",
                    "dependencies": [],
                    "conditions": {}
                },
                {
                    "tool_name": "validate_data",
                    "step_type": "parallel",
                    "dependencies": [],
                    "conditions": {},
                    "timeout_seconds": 30
                },
                {
                    "tool_name": "process_data",
                    "step_type": "sequential",
                    "dependencies": ["validate_data"],
                    "conditions": {
                        "allow_failed_dependencies": True
                    }
                },
                {
                    "tool_name": "backup_data",
                    "step_type": "sequential",
                    "dependencies": ["process_data"],
                    "conditions": {}
                }
            ]
        )
        
        self.templates["customer_onboarding"] = customer_onboarding
        self.templates["financial_processing"] = financial_processing
        self.templates["data_pipeline"] = data_pipeline
        self.templates["emergency_response"] = emergency_response
    
    def get_template(self, name: str) -> Optional[WorkflowTemplate]:
        return self.templates.get(name)
    
    def list_templates(self) -> List[Dict[str, str]]:
        return [
            {"name": name, "description": template.description}
            for name, template in self.templates.items()
        ]
    
    def add_template(self, template: WorkflowTemplate):
        self.templates[template.name] = template
    
    def remove_template(self, name: str) -> bool:
        if name in self.templates:
            del self.templates[name]
            return True
        return False
    
    def get_template_progress(self, template_name: str, completed_tools: List[str], 
                            failed_tools: List[str]) -> Dict[str, Any]:
        template = self.get_template(template_name)
        if not template:
            return {"error": "Template not found"}
        
        return template.get_progress(completed_tools, failed_tools)
    
    def get_next_steps(self, template_name: str, completed_tools: List[str], 
                      failed_tools: List[str], session_state: Dict[str, Any]) -> List[str]:
        template = self.get_template(template_name)
        if not template:
            return []
        
        executable_steps = template.get_next_executable_steps(completed_tools, failed_tools, session_state)
        return [step.tool_name for step in executable_steps]
    
    def validate_workflow_sequence(self, template_name: str, tool_sequence: List[str]) -> Dict[str, Any]:
        template = self.get_template(template_name)
        if not template:
            return {"valid": False, "error": "Template not found"}
        
        errors = []
        completed_tools = []
        
        for tool_name in tool_sequence:
            step = template.get_step_by_tool_name(tool_name)
            if not step:
                errors.append(f"Tool {tool_name} not found in template")
                continue
            
            if not step.can_execute(completed_tools, [], {}):
                missing_deps = [dep for dep in step.dependencies if dep not in completed_tools]
                errors.append(f"Tool {tool_name} missing dependencies: {missing_deps}")
            
            completed_tools.append(tool_name)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "completed_tools": completed_tools
        }