# Claude Context

This file contains context and instructions for Claude when working on this project.

## Project Status: COMPLETED ✅

Successfully built a comprehensive MCP Workflow Orchestrator proof of concept that demonstrates:
- ✅ Workflow monitoring and audit logging
- ✅ Policy-based execution ordering
- ✅ Comprehensive audit trail
- ✅ Real-time workflow status tracking
- ✅ Policy violation detection and blocking
- ✅ Approval gate workflows
- ✅ Template-based workflow management

## Quick Start

```bash
# Activate virtual environment
source venv/bin/activate

# Run all demos
python main.py demo

# Run specific demo
python main.py demo-success    # Successful workflow
python main.py demo-violation  # Policy violation demo
python main.py demo-approval   # Approval workflow demo

# Interactive mode
python main.py interactive

# Show system status
python main.py status
```

## Project Information

- **Project Name**: conductorio
- **Working Directory**: /Users/evansag/conductorio
- **Git Repository**: No

## Common Commands

Add commonly used commands here for reference:

```bash
python3
source venv/bin/activate
```

## Development Notes

### Anti-Patterns to Avoid
#### Don't Build:
Complex user interfaces
Production-grade persistence
Advanced authentication
Distributed workflow execution
Complex scheduling systems
Machine learning for workflow optimization

#### Do Build:
Clear workflow dependency logic
Comprehensive audit logging
Simple policy configuration
Easy workflow template creation
Real-time monitoring feedback

## Dependencies

Use a virtual python3 environment such as venv

Keep Dependencies Minimal:
fastapi==0.104.0
uvicorn==0.24.0
httpx==0.25.0
pydantic==2.4.0
rich==13.7.0  # For beautiful console output

## Architecture

Use These Technologies:

Python 3.9+ with asyncio
FastAPI for HTTP-based MCP servers (if needed)
In-memory data structures for POC (no databases)
Simple JSON files for workflow configuration
Standard library logging with structured output

2. Essential Components
Build these minimal components:
A. MCP Workflow Orchestrator (orchestrator.py)

Acts as MCP server to AI applications
Acts as MCP client to downstream servers
Enforces workflow policies and call ordering
Provides comprehensive audit logging
Tracks workflow state and dependencies

B. Workflow Policy Engine (workflow_policies.py)

Sequential Dependencies: Tool A must be called before Tool B
Parallel Restrictions: Some tools cannot run simultaneously
Conditional Execution: Tool C only available after Tool A succeeds
Workflow Templates: Predefined sequences for common operations
Approval Gates: Some tools require manual approval before execution

C. Audit Monitor (audit_monitor.py)

Comprehensive logging of all tool calls
Workflow compliance tracking
Performance metrics (duration, success rates)
Policy violation detection and reporting
Real-time workflow status

D. Example Downstream Servers (Workflow-focused)

Data Validation Server: Validates data before processing
Data Processing Server: Processes data (requires validation first)
Backup Server: Creates backups (should run after processing)
Notification Server: Sends notifications (final step)
Approval Server: Handles manual approval workflows

E. Demo CLI Application (demo.py)

Simulates AI application making workflow-based tool calls
Shows workflow enforcement and monitoring in action


condutorio
├── main.py                    # Main entry point
├── orchestrator.py            # Core workflow orchestrator
├── workflow_policies.py       # Workflow policy engine
├── audit_monitor.py          # Audit logging and monitoring
├── workflow_templates.py     # Predefined workflow templates
├── downstream_servers/
│   ├── validation_server.py  # Data validation MCP server
│   ├── processing_server.py  # Data processing MCP server
│   ├── backup_server.py      # Backup MCP server
│   ├── notification_server.py # Notification MCP server
│   └── approval_server.py    # Manual approval MCP server
├── demo_workflows.py         # Demo workflow scenarios
├── config.json              # Workflow and policy configuration
├── audit_logs/              # Directory for audit outputs
└── requirements.txt         # Minimal dependencies

5. Demonstration Script
Create a demo that shows:

Successful Workflow: AI app follows correct sequence
Dependency Enforcement: Blocking out-of-order tool calls
Audit Logging: Comprehensive tracking of all activities
Workflow Templates: Using predefined workflow patterns
Real-time Monitoring: Live workflow status and progress
Policy Violations: What happens when workflow rules are broken

## Key Principles

Keep it simple: Focus on demonstrating workflow orchestration and audit capabilities
No complex infrastructure: No Docker, Kubernetes, microservices, or distributed systems
Minimal dependencies: Use Python standard library where possible, add only essential packages
Easy to run: Should work with python main.py after minimal setup
Clear audit trail: Should provide comprehensive logging and monitoring of all MCP interactions

Remember: The goal is to demonstrate comprehensive workflow monitoring and audit capabilities, not to build a production workflow engine. Focus on showing the orchestration and audit value proposition clearly.

Console Dashboard:
┌─ Workflow Status Dashboard ─────────────────────┐
│ Active Workflows: 3                             │
│ Completed Today: 47                             │ 
│ Policy Violations: 2                            │
│                                                 │
│ Current Workflow: customer_onboarding          │
│ Progress: ████████░░ 80% (4/5 steps)           │
│ Duration: 3.2s                                  │
│ Next Step: send_notification                    │
└─────────────────────────────────────────────────┘