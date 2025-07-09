from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import json


class PolicyType(Enum):
    SEQUENTIAL_DEPENDENCY = "sequential_dependency"
    PARALLEL_RESTRICTION = "parallel_restriction"
    CONDITIONAL_EXECUTION = "conditional_execution"
    APPROVAL_REQUIRED = "approval_required"
    WORKFLOW_TEMPLATE = "workflow_template"


@dataclass
class PolicyResult:
    allowed: bool
    reason: str
    requires_approval: bool = False
    suggested_next_tools: List[str] = None
    
    def __post_init__(self):
        if self.suggested_next_tools is None:
            self.suggested_next_tools = []


class WorkflowPolicy:
    def __init__(self, policy_type: PolicyType, config: Dict[str, Any]):
        self.policy_type = policy_type
        self.config = config
    
    def evaluate(self, tool_name: str, completed_tools: List[str], session_state: Dict[str, Any]) -> PolicyResult:
        if self.policy_type == PolicyType.SEQUENTIAL_DEPENDENCY:
            return self._evaluate_sequential_dependency(tool_name, completed_tools)
        elif self.policy_type == PolicyType.PARALLEL_RESTRICTION:
            return self._evaluate_parallel_restriction(tool_name, completed_tools)
        elif self.policy_type == PolicyType.CONDITIONAL_EXECUTION:
            return self._evaluate_conditional_execution(tool_name, completed_tools, session_state)
        elif self.policy_type == PolicyType.APPROVAL_REQUIRED:
            return self._evaluate_approval_required(tool_name)
        else:
            return PolicyResult(allowed=True, reason="No policy applies")
    
    def _evaluate_sequential_dependency(self, tool_name: str, completed_tools: List[str]) -> PolicyResult:
        dependencies = self.config.get("dependencies", {})
        
        if tool_name in dependencies:
            required_tools = dependencies[tool_name]
            if isinstance(required_tools, str):
                required_tools = [required_tools]
            
            missing_deps = [dep for dep in required_tools if dep not in completed_tools]
            
            if missing_deps:
                return PolicyResult(
                    allowed=False,
                    reason=f"Missing required dependencies: {', '.join(missing_deps)}",
                    suggested_next_tools=missing_deps
                )
        
        return PolicyResult(allowed=True, reason="All dependencies satisfied")
    
    def _evaluate_parallel_restriction(self, tool_name: str, completed_tools: List[str]) -> PolicyResult:
        restrictions = self.config.get("restrictions", {})
        
        if tool_name in restrictions:
            conflicting_tools = restrictions[tool_name]
            if isinstance(conflicting_tools, str):
                conflicting_tools = [conflicting_tools]
            
            conflicts = [tool for tool in conflicting_tools if tool in completed_tools]
            
            if conflicts:
                return PolicyResult(
                    allowed=False,
                    reason=f"Cannot run in parallel with: {', '.join(conflicts)}"
                )
        
        return PolicyResult(allowed=True, reason="No parallel restrictions violated")
    
    def _evaluate_conditional_execution(self, tool_name: str, completed_tools: List[str], session_state: Dict[str, Any]) -> PolicyResult:
        conditions = self.config.get("conditions", {})
        
        if tool_name in conditions:
            condition = conditions[tool_name]
            
            # Check if required tool completed successfully
            if "requires_success" in condition:
                required_tool = condition["requires_success"]
                if required_tool not in completed_tools:
                    return PolicyResult(
                        allowed=False,
                        reason=f"Requires successful completion of {required_tool}"
                    )
                
                # Check if the result meets success criteria
                result_key = f"{required_tool}_result"
                if result_key in session_state:
                    result = session_state[result_key]
                    if not self._check_success_condition(result, condition.get("success_criteria", {})):
                        return PolicyResult(
                            allowed=False,
                            reason=f"Required tool {required_tool} did not meet success criteria"
                        )
        
        return PolicyResult(allowed=True, reason="Conditional requirements satisfied")
    
    def _evaluate_approval_required(self, tool_name: str) -> PolicyResult:
        required_tools = self.config.get("required_for", [])
        if isinstance(required_tools, str):
            required_tools = [required_tools]
        
        if tool_name in required_tools:
            return PolicyResult(
                allowed=True,
                reason="Manual approval required",
                requires_approval=True
            )
        
        return PolicyResult(allowed=True, reason="No approval required")
    
    def _check_success_condition(self, result: Any, criteria: Dict[str, Any]) -> bool:
        if not criteria:
            return True
        
        # Simple success criteria checking
        if "must_contain" in criteria:
            required_keys = criteria["must_contain"]
            if isinstance(required_keys, str):
                required_keys = [required_keys]
            
            if isinstance(result, dict):
                for key in required_keys:
                    if key not in result or not result[key]:
                        return False
        
        return True


class WorkflowTemplate:
    def __init__(self, name: str, steps: List[Dict[str, Any]]):
        self.name = name
        self.steps = steps
    
    def get_next_allowed_tools(self, completed_tools: List[str]) -> List[str]:
        allowed_tools = []
        
        for step in self.steps:
            tool_name = step["tool"]
            dependencies = step.get("dependencies", [])
            
            if tool_name not in completed_tools:
                # Check if all dependencies are satisfied
                if all(dep in completed_tools for dep in dependencies):
                    allowed_tools.append(tool_name)
        
        return allowed_tools
    
    def is_workflow_complete(self, completed_tools: List[str]) -> bool:
        required_tools = [step["tool"] for step in self.steps]
        return all(tool in completed_tools for tool in required_tools)


class WorkflowPolicyEngine:
    def __init__(self, config: Dict[str, Any]):
        self.policies: List[WorkflowPolicy] = []
        self.templates: Dict[str, WorkflowTemplate] = {}
        self._load_policies(config)
        self._load_templates(config)
    
    def _load_policies(self, config: Dict[str, Any]):
        policies_config = config.get("policies", {})
        
        # Load sequential dependencies
        if "sequential_dependencies" in policies_config:
            policy = WorkflowPolicy(
                PolicyType.SEQUENTIAL_DEPENDENCY,
                {"dependencies": policies_config["sequential_dependencies"]}
            )
            self.policies.append(policy)
        
        # Load parallel restrictions
        if "parallel_restrictions" in policies_config:
            policy = WorkflowPolicy(
                PolicyType.PARALLEL_RESTRICTION,
                {"restrictions": policies_config["parallel_restrictions"]}
            )
            self.policies.append(policy)
        
        # Load conditional execution rules
        if "conditional_execution" in policies_config:
            policy = WorkflowPolicy(
                PolicyType.CONDITIONAL_EXECUTION,
                {"conditions": policies_config["conditional_execution"]}
            )
            self.policies.append(policy)
        
        # Load approval requirements
        if "approval_required" in policies_config:
            policy = WorkflowPolicy(
                PolicyType.APPROVAL_REQUIRED,
                {"required_for": policies_config["approval_required"]}
            )
            self.policies.append(policy)
    
    def _load_templates(self, config: Dict[str, Any]):
        templates_config = config.get("workflow_templates", {})
        
        for template_name, template_config in templates_config.items():
            template = WorkflowTemplate(
                template_name,
                template_config.get("steps", [])
            )
            self.templates[template_name] = template
    
    def can_execute_tool(self, tool_name: str, completed_tools: List[str], session_state: Dict[str, Any]) -> PolicyResult:
        for policy in self.policies:
            result = policy.evaluate(tool_name, completed_tools, session_state)
            
            if not result.allowed:
                return result
            
            # If approval is required, we still allow execution but mark it
            if result.requires_approval:
                return result
        
        return PolicyResult(allowed=True, reason="All policies satisfied")
    
    def get_next_allowed_tools(self, completed_tools: List[str], active_template: Optional[str] = None) -> List[str]:
        if active_template and active_template in self.templates:
            return self.templates[active_template].get_next_allowed_tools(completed_tools)
        
        # If no template is active, return all tools that don't have unmet dependencies
        all_tools = {"validate_data", "process_data", "backup_data", "send_notification", "require_approval"}
        allowed_tools = []
        
        for tool in all_tools:
            if tool not in completed_tools:
                # Check if this tool can be executed given current state
                result = self.can_execute_tool(tool, completed_tools, {})
                if result.allowed:
                    allowed_tools.append(tool)
        
        return allowed_tools
    
    def get_workflow_progress(self, completed_tools: List[str], active_template: Optional[str] = None) -> Dict[str, Any]:
        if active_template and active_template in self.templates:
            template = self.templates[active_template]
            total_steps = len(template.steps)
            completed_steps = len([step for step in template.steps if step["tool"] in completed_tools])
            
            return {
                "template": active_template,
                "total_steps": total_steps,
                "completed_steps": completed_steps,
                "progress_percent": (completed_steps / total_steps) * 100 if total_steps > 0 else 0,
                "is_complete": template.is_workflow_complete(completed_tools),
                "next_allowed_tools": template.get_next_allowed_tools(completed_tools)
            }
        
        return {
            "template": None,
            "total_steps": 0,
            "completed_steps": len(completed_tools),
            "progress_percent": 0,
            "is_complete": False,
            "next_allowed_tools": self.get_next_allowed_tools(completed_tools)
        }