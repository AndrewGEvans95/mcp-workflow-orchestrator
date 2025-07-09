import asyncio
import argparse
import sys
import logging
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from demo_workflows import WorkflowDemo
from orchestrator import MCPOrchestrator
from workflow_templates import WorkflowTemplateManager


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('audit_logs/orchestrator.log'),
            logging.StreamHandler()
        ]
    )


def print_banner():
    """Print the application banner."""
    console = Console()
    banner = """
    ███╗   ███╗ ██████╗██████╗      ██████╗ ██████╗  ██████╗██╗  ██╗███████╗███████╗████████╗██████╗  █████╗ ████████╗ ██████╗ ██████╗ 
    ████╗ ████║██╔════╝██╔══██╗    ██╔═══██╗██╔══██╗██╔════╝██║  ██║██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗
    ██╔████╔██║██║     ██████╔╝    ██║   ██║██████╔╝██║     ███████║█████╗  ███████╗   ██║   ██████╔╝███████║   ██║   ██║   ██║██████╔╝
    ██║╚██╔╝██║██║     ██╔═══╝     ██║   ██║██╔══██╗██║     ██╔══██║██╔══╝  ╚════██║   ██║   ██╔══██╗██╔══██║   ██║   ██║   ██║██╔══██╗
    ██║ ╚═╝ ██║╚██████╗██║         ╚██████╔╝██║  ██║╚██████╗██║  ██║███████╗███████║   ██║   ██║  ██║██║  ██║   ██║   ╚██████╔╝██║  ██║
    ╚═╝     ╚═╝ ╚═════╝╚═╝          ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝
    """
    
    console.print(Panel(
        Text(banner, style="bold cyan"),
        title="MCP Workflow Orchestrator",
        subtitle="Proof of Concept - Workflow Monitoring & Audit System",
        style="blue"
    ))


def print_help():
    """Print help information."""
    console = Console()
    help_text = """
    [bold cyan]MCP Workflow Orchestrator - Usage Guide[/bold cyan]
    
    [bold]Available Commands:[/bold]
    
    [yellow]Demo Commands:[/yellow]
    • demo                 - Run all demo workflows
    • demo-success         - Run successful workflow demo
    • demo-violation       - Run policy violation demo
    • demo-approval        - Run approval workflow demo
    • demo-monitoring      - Run real-time monitoring demo
    • demo-audit           - Run comprehensive audit demo
    
    [yellow]Interactive Commands:[/yellow]
    • interactive          - Start interactive mode
    • status               - Show system status
    • templates            - List available workflow templates
    • help                 - Show this help message
    
    [bold]Example Usage:[/bold]
    
    [green]# Run all demos[/green]
    python main.py demo
    
    [green]# Run specific demo[/green]
    python main.py demo-success
    
    [green]# Start interactive mode[/green]
    python main.py interactive
    
    [green]# Show system status[/green]
    python main.py status
    
    [bold]System Requirements:[/bold]
    • Python 3.9+
    • Virtual environment activated
    • All dependencies installed (see requirements.txt)
    
    [bold]Key Features Demonstrated:[/bold]
    ✓ Workflow orchestration and policy enforcement
    ✓ Comprehensive audit logging and monitoring
    ✓ Real-time workflow status tracking
    ✓ Policy violation detection and blocking
    ✓ Approval gate workflows
    ✓ Template-based workflow management
    """
    
    console.print(Panel(help_text, title="Help", style="green"))


async def run_demo(demo_type: str = "all"):
    """Run demonstration workflows."""
    demo = WorkflowDemo()
    
    if demo_type == "all":
        await demo.run_all_demos()
    elif demo_type == "success":
        await demo.demo_successful_workflow()
    elif demo_type == "violation":
        await demo.demo_policy_violation()
    elif demo_type == "approval":
        await demo.demo_approval_workflow()
    elif demo_type == "monitoring":
        await demo.demo_real_time_monitoring()
    elif demo_type == "audit":
        await demo.demo_comprehensive_audit()
    else:
        print(f"Unknown demo type: {demo_type}")
        return


async def show_status():
    """Show system status."""
    console = Console()
    orchestrator = MCPOrchestrator()
    template_manager = WorkflowTemplateManager()
    
    # System status
    console.print(Panel(
        "[bold green]System Status: Operational[/bold green]\n"
        "• MCP Orchestrator: Running\n"
        "• Audit Monitor: Active\n"
        "• Policy Engine: Loaded\n"
        "• Template Manager: Ready",
        title="System Status"
    ))
    
    # Available templates
    templates = template_manager.list_templates()
    if templates:
        console.print("\n[bold]Available Workflow Templates:[/bold]")
        for template in templates:
            console.print(f"• {template['name']}: {template['description']}")
    
    # Active sessions
    sessions = orchestrator.get_all_sessions_status()
    if sessions:
        console.print(f"\n[bold]Active Sessions:[/bold] {len(sessions)}")
        for session in sessions[-5:]:  # Show last 5
            console.print(f"• {session['session_id']}: {session['total_calls']} calls")
    else:
        console.print("\n[bold]Active Sessions:[/bold] None")


async def interactive_mode():
    """Start interactive mode."""
    console = Console()
    orchestrator = MCPOrchestrator()
    template_manager = WorkflowTemplateManager()
    
    console.print(Panel(
        "[bold cyan]Interactive Mode[/bold cyan]\n"
        "Type 'help' for available commands, 'exit' to quit",
        title="Interactive Mode"
    ))
    
    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if command == "exit":
                console.print("[yellow]Goodbye![/yellow]")
                break
            elif command == "help":
                console.print("""
[bold]Interactive Commands:[/bold]
• status        - Show system status
• templates     - List workflow templates
• sessions      - List active sessions
• audit         - Show audit summary
• demo <type>   - Run specific demo (success, violation, approval, monitoring, audit)
• clear         - Clear screen
• exit          - Exit interactive mode
                """)
            elif command == "status":
                await show_status()
            elif command == "templates":
                templates = template_manager.list_templates()
                for template in templates:
                    console.print(f"• {template['name']}: {template['description']}")
            elif command == "sessions":
                sessions = orchestrator.get_all_sessions_status()
                if sessions:
                    for session in sessions:
                        console.print(f"• {session['session_id']}: {session['total_calls']} calls")
                else:
                    console.print("No active sessions")
            elif command == "audit":
                demo = WorkflowDemo()
                await demo.demo_comprehensive_audit()
            elif command.startswith("demo "):
                demo_type = command.split(" ", 1)[1]
                await run_demo(demo_type)
            elif command == "clear":
                console.clear()
            elif command == "":
                continue
            else:
                console.print(f"[red]Unknown command: {command}[/red]")
                console.print("Type 'help' for available commands")
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' to quit[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MCP Workflow Orchestrator - Proof of Concept",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        default="help",
        help="Command to execute (demo, interactive, status, templates, help)"
    )
    
    parser.add_argument(
        "--demo-type",
        choices=["all", "success", "violation", "approval", "monitoring", "audit"],
        default="all",
        help="Type of demo to run (default: all)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Print banner
    print_banner()
    
    # Execute command
    if args.command == "help":
        print_help()
    elif args.command == "demo":
        asyncio.run(run_demo(args.demo_type))
    elif args.command == "demo-success":
        asyncio.run(run_demo("success"))
    elif args.command == "demo-violation":
        asyncio.run(run_demo("violation"))
    elif args.command == "demo-approval":
        asyncio.run(run_demo("approval"))
    elif args.command == "demo-monitoring":
        asyncio.run(run_demo("monitoring"))
    elif args.command == "demo-audit":
        asyncio.run(run_demo("audit"))
    elif args.command == "interactive":
        asyncio.run(interactive_mode())
    elif args.command == "status":
        asyncio.run(show_status())
    elif args.command == "templates":
        template_manager = WorkflowTemplateManager()
        templates = template_manager.list_templates()
        console = Console()
        console.print("[bold]Available Workflow Templates:[/bold]")
        for template in templates:
            console.print(f"• {template['name']}: {template['description']}")
    else:
        print(f"Unknown command: {args.command}")
        print("Use 'python main.py help' for available commands")
        sys.exit(1)


if __name__ == "__main__":
    main()