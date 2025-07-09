import asyncio
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
import time

from orchestrator import MCPOrchestrator
from workflow_templates import WorkflowTemplateManager


class WorkflowDemo:
    def __init__(self):
        self.console = Console()
        self.orchestrator = MCPOrchestrator()
        self.template_manager = WorkflowTemplateManager()
        self.logger = logging.getLogger(__name__)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
    
    def print_header(self, title: str):
        self.console.print(Panel(
            Text(title, style="bold cyan"),
            style="blue",
            padding=(1, 2)
        ))
    
    def print_workflow_status(self, session_id: str, workflow_name: str = None):
        session_status = self.orchestrator.get_session_status(session_id)
        
        if workflow_name:
            template = self.template_manager.get_template(workflow_name)
            if template:
                progress = template.get_progress(
                    session_status["completed_tools"],
                    session_status["failed_tools"]
                )
                
                # Create progress bar
                progress_bar = "█" * int(progress["progress_percent"] / 10) + "░" * (10 - int(progress["progress_percent"] / 10))
                
                status_table = Table(title=f"Workflow Status: {workflow_name}")
                status_table.add_column("Metric", style="cyan")
                status_table.add_column("Value", style="green")
                
                status_table.add_row("Session ID", session_id)
                status_table.add_row("Progress", f"{progress_bar} {progress['progress_percent']:.1f}%")
                status_table.add_row("Completed Steps", f"{progress['completed_steps']}/{progress['total_steps']}")
                status_table.add_row("Failed Steps", str(progress['failed_steps']))
                status_table.add_row("Total Tool Calls", str(session_status["total_calls"]))
                
                self.console.print(status_table)
        
        # Show recent events
        recent_events = self.orchestrator.audit_monitor.get_recent_events(session_id, limit=5)
        if recent_events:
            events_table = Table(title="Recent Events")
            events_table.add_column("Time", style="cyan")
            events_table.add_column("Event", style="yellow")
            events_table.add_column("Tool", style="green")
            events_table.add_column("Message", style="white")
            
            for event in recent_events:
                timestamp = datetime.fromisoformat(event["timestamp"]).strftime("%H:%M:%S")
                events_table.add_row(
                    timestamp,
                    event["event_type"],
                    event.get("tool_name", ""),
                    event["message"][:50] + "..." if len(event["message"]) > 50 else event["message"]
                )
            
            self.console.print(events_table)
    
    async def demo_successful_workflow(self):
        self.print_header("Demo 1: Successful Customer Onboarding Workflow")
        
        session_id = f"demo_success_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workflow_name = "customer_onboarding"
        
        # Sample customer data
        customer_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "555-123-4567",
            "account_type": "premium"
        }
        
        self.console.print(f"[bold]Starting workflow: {workflow_name}[/bold]")
        self.console.print(f"Customer data: {json.dumps(customer_data, indent=2)}")
        
        # Get workflow template
        template = self.template_manager.get_template(workflow_name)
        if not template:
            self.console.print("[red]Error: Workflow template not found[/red]")
            return
        
        # Execute workflow steps
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            workflow_task = progress.add_task("Executing workflow...", total=len(template.steps))
            
            for step in template.steps:
                step_task = progress.add_task(f"Executing {step.tool_name}...", total=1)
                
                # Execute the tool
                result = await self.orchestrator.call_tool(
                    session_id, 
                    step.tool_name, 
                    {"data": customer_data}
                )
                
                if result["success"]:
                    self.console.print(f"[green]✓ {step.tool_name} completed successfully[/green]")
                    # Update customer data with result if needed
                    if "result" in result and isinstance(result["result"], dict):
                        if "validated_data" in result["result"]:
                            customer_data.update(result["result"]["validated_data"])
                        elif "processed_data" in result["result"]:
                            customer_data.update(result["result"]["processed_data"])
                else:
                    self.console.print(f"[red]✗ {step.tool_name} failed: {result['error']}[/red]")
                
                progress.update(step_task, completed=1)
                progress.update(workflow_task, advance=1)
                
                # Small delay for demo effect
                await asyncio.sleep(0.5)
        
        self.print_workflow_status(session_id, workflow_name)
        
        # Show final audit report
        compliance_report = self.orchestrator.audit_monitor.generate_compliance_report(session_id)
        self.console.print(f"\n[bold]Compliance Report:[/bold]")
        self.console.print(f"Success Rate: {compliance_report['summary']['success_rate']:.1%}")
        self.console.print(f"Policy Violations: {compliance_report['summary']['policy_violations']}")
        self.console.print(f"Compliance Score: {compliance_report['summary']['compliance_score']}")
    
    async def demo_policy_violation(self):
        self.print_header("Demo 2: Policy Violation - Dependency Enforcement")
        
        session_id = f"demo_violation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.console.print("[bold]Attempting to process data without validation (should be blocked)[/bold]")
        
        # Try to process data without validation first
        result = await self.orchestrator.call_tool(
            session_id,
            "process_data",
            {"data": {"name": "Test User"}}
        )
        
        if not result["success"]:
            self.console.print(f"[red]✗ Blocked: {result['error']}[/red]")
        else:
            self.console.print(f"[green]✓ Unexpectedly allowed[/green]")
        
        # Show policy violations
        violations = self.orchestrator.audit_monitor.get_policy_violations(session_id)
        if violations:
            violations_table = Table(title="Policy Violations")
            violations_table.add_column("Time", style="cyan")
            violations_table.add_column("Tool", style="yellow")
            violations_table.add_column("Violation", style="red")
            
            for violation in violations:
                timestamp = datetime.fromisoformat(violation["timestamp"]).strftime("%H:%M:%S")
                violations_table.add_row(
                    timestamp,
                    violation.get("tool_name", ""),
                    violation["message"]
                )
            
            self.console.print(violations_table)
        
        # Now do it correctly
        self.console.print("\n[bold]Doing it correctly: validate first, then process[/bold]")
        
        # Validate first
        result1 = await self.orchestrator.call_tool(
            session_id,
            "validate_data",
            {"data": {"name": "Test User"}}
        )
        
        if result1["success"]:
            self.console.print("[green]✓ Validation completed[/green]")
        
        # Now process
        result2 = await self.orchestrator.call_tool(
            session_id,
            "process_data",
            {"data": {"name": "Test User"}}
        )
        
        if result2["success"]:
            self.console.print("[green]✓ Processing completed[/green]")
        
        self.print_workflow_status(session_id)
    
    async def demo_approval_workflow(self):
        self.print_header("Demo 3: Financial Processing with Approval Gate")
        
        session_id = f"demo_approval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workflow_name = "financial_processing"
        
        financial_data = {
            "amount": 50000.00,
            "account_number": "123456789",
            "transaction_type": "wire_transfer",
            "destination": "external_bank"
        }
        
        self.console.print(f"[bold]Starting financial processing workflow[/bold]")
        self.console.print(f"Transaction data: {json.dumps(financial_data, indent=2)}")
        
        # Get workflow template
        template = self.template_manager.get_template(workflow_name)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            workflow_task = progress.add_task("Executing financial workflow...", total=len(template.steps))
            
            for step in template.steps:
                step_task = progress.add_task(f"Executing {step.tool_name}...", total=1)
                
                # Prepare arguments based on step
                if step.tool_name == "require_approval":
                    args = {
                        "requested_action": "high_value_transfer",
                        "approval_level": "elevated",
                        "justification": f"Wire transfer of ${financial_data['amount']} to external bank",
                        "metadata": financial_data
                    }
                else:
                    args = {"data": financial_data}
                
                # Execute the tool
                result = await self.orchestrator.call_tool(session_id, step.tool_name, args)
                
                if result["success"]:
                    self.console.print(f"[green]✓ {step.tool_name} completed successfully[/green]")
                    
                    # Show approval details if this was an approval step
                    if step.tool_name == "require_approval" and "result" in result:
                        approval_result = result["result"]
                        self.console.print(f"   Approval ID: {approval_result.get('approval_id', 'N/A')}")
                        self.console.print(f"   Approved: {approval_result.get('approved', False)}")
                        self.console.print(f"   Approved by: {approval_result.get('approval_decision', {}).get('approved_by', 'N/A')}")
                else:
                    self.console.print(f"[red]✗ {step.tool_name} failed: {result['error']}[/red]")
                
                progress.update(step_task, completed=1)
                progress.update(workflow_task, advance=1)
                
                await asyncio.sleep(0.5)
        
        self.print_workflow_status(session_id, workflow_name)
    
    async def demo_real_time_monitoring(self):
        self.print_header("Demo 4: Real-time Workflow Monitoring")
        
        session_id = f"demo_monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workflow_name = "data_pipeline"
        
        # Create layout for real-time monitoring
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=5)
        )
        
        # Sample data for processing
        pipeline_data = {
            "batch_id": "batch_20240101_001",
            "record_count": 10000,
            "data_source": "customer_database",
            "processing_type": "analytics"
        }
        
        template = self.template_manager.get_template(workflow_name)
        
        with Live(layout, console=self.console, screen=False, refresh_per_second=2) as live:
            # Update header
            layout["header"].update(Panel(
                Text("Real-time Workflow Monitoring Dashboard", style="bold cyan"),
                style="blue"
            ))
            
            for i, step in enumerate(template.steps):
                # Update main area with current step
                progress_text = f"Step {i+1}/{len(template.steps)}: {step.tool_name}"
                progress_bar = "█" * (i * 10 // len(template.steps)) + "░" * (10 - (i * 10 // len(template.steps)))
                
                layout["main"].update(Panel(
                    f"{progress_text}\n\n{progress_bar} {(i / len(template.steps) * 100):.1f}%\n\nProcessing...",
                    title="Current Status"
                ))
                
                # Execute step
                result = await self.orchestrator.call_tool(
                    session_id,
                    step.tool_name,
                    {"data": pipeline_data}
                )
                
                # Update footer with session status
                session_status = self.orchestrator.get_session_status(session_id)
                footer_text = f"Session: {session_id}\n"
                footer_text += f"Completed: {len(session_status['completed_tools'])}\n"
                footer_text += f"Failed: {len(session_status['failed_tools'])}\n"
                footer_text += f"Total Calls: {session_status['total_calls']}\n"
                
                layout["footer"].update(Panel(footer_text, title="Session Metrics"))
                
                # Brief delay for demo effect
                await asyncio.sleep(1)
            
            # Final update
            layout["main"].update(Panel(
                "Workflow Complete!\n\n██████████ 100%\n\nAll steps executed successfully",
                title="Final Status",
                style="green"
            ))
            
            # Hold for a moment to show completion
            await asyncio.sleep(2)
    
    async def demo_comprehensive_audit(self):
        self.print_header("Demo 5: Comprehensive Audit Trail")
        
        # Show audit data from all previous demos
        all_sessions = self.orchestrator.get_all_sessions_status()
        
        if not all_sessions:
            self.console.print("[yellow]No sessions found. Run other demos first.[/yellow]")
            return
        
        # Create audit summary table
        audit_table = Table(title="Audit Summary - All Sessions")
        audit_table.add_column("Session ID", style="cyan")
        audit_table.add_column("Total Calls", style="green")
        audit_table.add_column("Completed", style="green")
        audit_table.add_column("Failed", style="red")
        audit_table.add_column("Start Time", style="yellow")
        
        for session in all_sessions:
            audit_table.add_row(
                session["session_id"],
                str(session["total_calls"]),
                str(len(session["completed_tools"])),
                str(len(session["failed_tools"])),
                session["start_time"][:19] if session["start_time"] else "N/A"
            )
        
        self.console.print(audit_table)
        
        # Show policy violations across all sessions
        all_violations = self.orchestrator.audit_monitor.get_policy_violations()
        if all_violations:
            violations_table = Table(title="Policy Violations - All Sessions")
            violations_table.add_column("Session", style="cyan")
            violations_table.add_column("Time", style="yellow")
            violations_table.add_column("Tool", style="red")
            violations_table.add_column("Violation", style="white")
            
            for violation in all_violations[-10:]:  # Show last 10
                timestamp = datetime.fromisoformat(violation["timestamp"]).strftime("%H:%M:%S")
                violations_table.add_row(
                    violation["session_id"],
                    timestamp,
                    violation.get("tool_name", ""),
                    violation["message"][:50] + "..." if len(violation["message"]) > 50 else violation["message"]
                )
            
            self.console.print(violations_table)
        
        # Show performance metrics
        performance_metrics = self.orchestrator.audit_monitor.get_tool_performance_metrics()
        if performance_metrics:
            perf_table = Table(title="Tool Performance Metrics")
            perf_table.add_column("Tool", style="cyan")
            perf_table.add_column("Calls", style="green")
            perf_table.add_column("Avg Duration", style="yellow")
            perf_table.add_column("Total Duration", style="white")
            
            for tool, metrics in performance_metrics.items():
                perf_table.add_row(
                    tool,
                    str(metrics["call_count"]),
                    f"{metrics['avg_duration']:.2f}s",
                    f"{metrics['total_duration']:.2f}s"
                )
            
            self.console.print(perf_table)
    
    async def run_all_demos(self):
        self.console.print(Panel(
            Text("MCP Workflow Orchestrator - Complete Demo Suite", style="bold magenta"),
            style="magenta",
            padding=(1, 2)
        ))
        
        demos = [
            ("Successful Workflow", self.demo_successful_workflow),
            ("Policy Violation", self.demo_policy_violation),
            ("Approval Workflow", self.demo_approval_workflow),
            ("Real-time Monitoring", self.demo_real_time_monitoring),
            ("Comprehensive Audit", self.demo_comprehensive_audit)
        ]
        
        for demo_name, demo_func in demos:
            self.console.print(f"\n[bold blue]Running: {demo_name}[/bold blue]")
            await demo_func()
            self.console.print("\n" + "="*60 + "\n")
            await asyncio.sleep(1)
        
        self.console.print(Panel(
            Text("All demos completed successfully!", style="bold green"),
            style="green",
            padding=(1, 2)
        ))


if __name__ == "__main__":
    demo = WorkflowDemo()
    asyncio.run(demo.run_all_demos())