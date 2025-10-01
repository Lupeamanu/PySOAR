""" Command Line Interface for PySOAR """

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.playbook_engine import PlaybookEngine
from core.integration_manager import IntegrationManager
from core.case_manager import CaseManager
from models.case import Status, Severity


class PySOARCLI:
    """ Command Line Interface for PySOAR """

    def __init__(self) -> None:
        self.integration_manager = None
        self.engine = None


    def run(self):
        """ Main entry point for the CLI """
        parser = argparse.ArgumentParser(
            description="PySOAR - Security Orchestration, Automation & Response",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
    # Run a playbook
    python -m src.cli.cli run -p config/playbooks/ip_investigation.yaml -i ip_address=8.8.8.8

    # List available playbooks
    python -m src.cli.cli list

    # List integrations
    python -m src.cli.cli integrations
            """
        )

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Run command
        run_parser = subparsers.add_parser("run", help="Run a playbook")
        run_parser.add_argument("-p", "--playbook", required=True, help="Pat hto the playbook YAML file")
        run_parser.add_argument("-i", "--input", action="append", help="Input parameters (key=value)")
        run_parser.add_argument("-c", "--config", default="config/integrations.yaml", help="Integration config file")
        run_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
        run_parser.add_argument("-o", "--output", help="Save results to JSON file")

        # List command
        list_parser = subparsers.add_parser("list", help="List available playbooks")
        list_parser.add_argument("-d", "--directory", default="config/playbooks", help="Playbooks directory")

        # Integrations command
        int_parser = subparsers.add_parser("integrations", help="List loaded integrations")
        int_parser.add_argument("-c", "--config", default="config/integrations.yaml", help="Integration config file")

        # Case commands
        case_parser = subparsers.add_parser("case", help="Case management commands")
        case_subparsers = case_parser.add_subparsers(dest="case_command")

        # Create case
        create_case = case_subparsers.add_parser("create", help="Create a new case")
        create_case.add_argument("-t", "--title", required=True, help="Case title")
        create_case.add_argument("-d", "--description", default='', help="Case description")
        create_case.add_argument("-s", "--severity", choices=["low", "medium", "high", "critical"], default="medium", help="Case severity")
        create_case.add_argument("--tags", help="Comma-separated tags")

        # List cases
        list_cases = case_subparsers.add_parser("list", help="List cases")
        list_cases.add_argument("--status", choices=["open", "investigating", "resolved", "closed"], help="Filter by status")
        list_cases.add_argument("--severity", choices=["low", "medium", "high", "critical"], help="Filter by severity")
        list_cases.add_argument("-n", "--limit", type=int, default=20, help="Number of cases to show")

        # View case
        view_case = case_subparsers.add_parser("view", help="View case details")
        view_case.add_argument("case_id", help="Case ID")

        # Update case
        update_case = case_subparsers.add_parser("update", help="Update case")
        update_case.add_argument("case_id", help="Case ID")
        update_case.add_argument("--status", choices=["open", "investigating", "resolved", "closed"], help="Update status")
        update_case.add_argument("--severity", choices=["low", "medium", "high", "critical"], help="Update severity")
        update_case.add_argument("--comment", help="Add a comment")

        # Case stats
        stats_case = case_subparsers.add_parser("stats", help="Show case statistics")

        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            return

        # Route to appropriate command handler
        if args.command == "run":
            self.handle_run(args)
        elif args.command == "list":
            self.handle_list(args)
        elif args.command == "integrations":
            self.handle_integrations(args)
        elif args.command == "case":
            self.handle_case(args)


    def handle_run(self, args):
        """ Handle the run command """
        self._print_header("PySOAR Playbook Execution")

        # Parse inputs
        inputs = {}
        if args.input:
            for inp in args.input:
                if '=' in inp:
                    key, value = inp.split('=', 1)
                    inputs[key.strip()] = value.strip()

        print(f"Playbook: {args.playbook}")
        print(f"Config: {args.config}")
        if inputs:
            print(f"Inputs: {inputs}")
        print()

        try:
            # Initialize integration manager
            print("Loading integrations...")
            self.integration_manager = IntegrationManager(args.config)
            integrations = self.integration_manager.list_integrations()
            print(f"Loaded: {', '.join(integrations) if integrations else 'None'}\n")

            # Initialize the engine
            self.engine = PlaybookEngine(integration_manager=self.integration_manager)

            # Load playbook
            print("Loading playbook...")
            playbook = self.engine.load_playbook(args.playbook)
            print(f"Name: {playbook.name}")
            print(f"Description: {playbook.description}")
            print(f"Actions: {len(playbook.actions)}\n")

            # Execute the playbook
            print("Executing the playbook...\n")
            print("=" * 70)

            result = self.engine.execute(playbook, inputs=inputs)

            print("=" * 70)
            print()

            # Display results
            self._display_results(result, verbose=args.verbose)

            # Save to file if requested
            if args.output:
                self._save_results(result, args.output)

        except FileNotFoundError as e:
            print(f"Error: File not found - {e}")
        except Exception as e:
            print(f"Error: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)


    def handle_list(self, args):
        """ Handle the list command """
        self._print_header("Available Playbooks")

        playbooks_dir = Path(args.directory)

        if not playbooks_dir.exists():
            print(f"Directory not found: {playbooks_dir}")
            return

        playbooks = list(playbooks_dir.glob("*.yaml")) + list(playbooks_dir.glob("*.yml"))

        if not playbooks:
            print(f"No playbooks found in {playbooks_dir}")
            return

        for pb in sorted(playbooks):
            try:
                # Try to load and get basic info
                engine = PlaybookEngine()
                playbook = engine.load_playbook(str(pb))
                print(f"{pb.name}")
                print(f"  Name: {playbook.name}")
                print(f"  Description: {playbook.description}")
                print(f"  Inputs: {', '.join(playbook.inputs) if playbook.inputs else 'None'}")
                print(f"  Actions: {len(playbook.actions)}")
                print()
            except Exception as e:
                print(f"{pb.name} - Error loading: {e}\n")


    def handle_integrations(self, args):
        """ Handle the integrations command """
        self._print_header("Integrations Status")

        try:
            integration_manager = IntegrationManager(args.config)
            integrations = integration_manager.list_integrations()

            if not integrations:
                print("No integrations loaded")
                print(f"Check your config file: {args.config}")
                return

            print(f"Loaded {len(integrations)} integration(s):\n")

            for name in integrations:
                integration = integration_manager.get_integration(name)
                actions = integration.get_available_actions() # type: ignore

                print(name)
                print(f"  Actions: {', '.join(actions)}")
                print(f"  Status: {'API Key Configured' if integration.api_key else 'Using Mock Data'}") # type: ignore
                print()

        except FileNotFoundError:
            print(f"Config file not found: {args.config}")
        except Exception as e:
            print(f"Error loading integrations: {e}")


    def handle_case(self, args):
        """Handle case management commands"""
        if not args.case_command:
            print("❌ Please specify a case command. Use --help for options.")
            return
        
        case_manager = CaseManager()
        
        if args.case_command == 'create':
            self._case_create(case_manager, args)
        elif args.case_command == 'list':
            self._case_list(case_manager, args)
        elif args.case_command == 'view':
            self._case_view(case_manager, args)
        elif args.case_command == 'update':
            self._case_update(case_manager, args)
        elif args.case_command == 'stats':
            self._case_stats(case_manager)

    
    def _case_create(self, case_manager, args):
        """Create a new case"""
        self._print_header("Create New Case")
        
        tags = []
        if args.tags:
            tags = [t.strip() for t in args.tags.split(',')]
        
        case = case_manager.create_case(
            title=args.title,
            description=args.description,
            severity=args.severity,
            tags=tags
        )
        
        print(f"✅ Case created successfully!")
        print(f"   ID: {case.id}")
        print(f"   Title: {case.title}")
        print(f"   Severity: {case.severity.upper()}")
        print(f"   Status: {case.status}")
        if tags:
            print(f"   Tags: {', '.join(tags)}")

    
    def _case_list(self, case_manager, args):
        """List cases"""
        self._print_header("Cases")
        
        cases = case_manager.list_cases(
            status=args.status,
            severity=args.severity,
            limit=args.limit
        )
        
        if not cases:
            print("No cases found.")
            return
        
        print(f"Found {len(cases)} case(s):\n")
        
        for case in cases:
            # Status and severity indicators
            status_icon = {
                'open': '🔴',
                'investigating': '🟡',
                'resolved': '🟢',
                'closed': '⚪'
            }.get(case.status, '⚫')
            
            severity_icon = {
                'critical': '🔥',
                'high': '⚠️ ',
                'medium': '📋',
                'low': '📝'
            }.get(case.severity, '📋')
            
            print(f"{status_icon} {severity_icon} [{case.id[:8]}] {case.title}")
            print(f"   Status: {case.status.upper()} | Severity: {case.severity.upper()}")
            print(f"   Created: {case.created_at.strftime('%Y-%m-%d %H:%M')}")
            if case.artifacts:
                print(f"   Artifacts: {len(case.artifacts)}")
            if case.playbooks_executed:
                print(f"   Playbooks: {len(case.playbooks_executed)}")
            print()

    
    def _case_view(self, case_manager, args):
        """View case details"""
        case = case_manager.get_case(args.case_id)
        
        if not case:
            print(f"❌ Case not found: {args.case_id}")
            return
        
        self._print_header(f"Case Details: {case.title}")
        
        print(f"ID: {case.id}")
        print(f"Title: {case.title}")
        print(f"Description: {case.description or 'N/A'}")
        print(f"Severity: {case.severity.upper()}")
        print(f"Status: {case.status.upper()}")
        print(f"Created: {case.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Updated: {case.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if case.assigned_to:
            print(f"Assigned To: {case.assigned_to}")
        if case.tags:
            print(f"Tags: {', '.join(case.tags)}")
        print()
        
        # Artifacts
        if case.artifacts:
            print("📎 Artifacts:")
            print("-" * 70)
            for artifact in case.artifacts:
                print(f"  [{artifact.artifact_type}] {artifact.value}")
                if artifact.description:
                    print(f"    Description: {artifact.description}")
            print()
        
        # Playbooks
        if case.playbooks_executed:
            print("🔄 Playbooks Executed:")
            print("-" * 70)
            for pb in case.playbooks_executed:
                print(f"  - {pb}")
            print()
        
        # Timeline
        print("📅 Timeline:")
        print("-" * 70)
        for event in case.events[-10:]:  # Show last 10 events
            timestamp = event.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            print(f"  [{timestamp}] {event.description}")
        
        if len(case.events) > 10:
            print(f"\n  ... and {len(case.events) - 10} more events")

    
    def _case_update(self, case_manager, args):
        """Update a case"""
        case = case_manager.get_case(args.case_id)
        
        if not case:
            print(f"❌ Case not found: {args.case_id}")
            return
        
        updated = False
        
        if args.status:
            case.update_status(args.status)
            print(f"✅ Updated status to: {args.status.upper()}")
            updated = True
        
        if args.severity:
            case.update_severity(args.severity)
            print(f"✅ Updated severity to: {args.severity.upper()}")
            updated = True
        
        if args.comment:
            case.add_comment(args.comment)
            print(f"✅ Added comment")
            updated = True
        
        if updated:
            case_manager.update_case(case)
            print(f"\n📋 Case {case.id[:8]} updated successfully")
        else:
            print("⚠️  No updates specified")

    
    def _case_stats(self, case_manager):
        """Show case statistics"""
        self._print_header("Case Statistics")
        
        stats = case_manager.get_statistics()
        
        print(f"Total Cases: {stats['total']}")
        print(f"Open Cases: {stats['open']}")
        print()
        
        print("By Status:")
        for status, count in stats['by_status'].items():
            print(f"  {status.upper()}: {count}")
        print()
        
        print("By Severity:")
        for severity, count in stats['by_severity'].items():
            print(f"  {severity.upper()}: {count}")

    
    def _display_results(self, result, verbose=False):
        """Display execution results"""
        status = result['status']
        
        if status == 'SUCCESS':
            print("✅ Execution Status: SUCCESS")
        else:
            print("❌ Execution Status: FAILED")
            if result.get('error'):
                print(f"   Error: {result['error']}")
        
        print(f"⏱️  Duration: {result['duration_seconds']:.2f}s")
        print()
        
        # Display context variables
        context = result.get('context', {})
        if context:
            print("📊 Results:")
            print("-" * 70)
            for key, value in context.items():
                if key == 'inputs':
                    continue
                if isinstance(value, dict) and len(str(value)) > 100:
                    print(f"   {key}: [complex object]")
                else:
                    print(f"   {key}: {value}")
            print()
        
        # Show execution log if verbose
        if verbose and result.get('execution_log'):
            print("📝 Execution Log:")
            print("-" * 70)
            for entry in result['execution_log']:
                timestamp = entry['timestamp'].split('T')[1].split('.')[0]
                level = entry['level']
                message = entry['message']
                print(f"[{timestamp}] [{level}] {message}")
            print()


    def _save_results(self, result, output_file):
        """ Save results to JSON file """
        try:
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"Results saved to: {output_file}")
        except Exception as e:
            print(f"Failed to save results to: {e}")


    def _print_header(self, title):
        """ Print a formatted header """
        print()
        print("=" * 70)
        print(f"  {title}")
        print("=" * 70)
        print()


def main():
    cli = PySOARCLI()
    cli.run()


if __name__ == "__main__":
    main()