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


    def _display_results(self, result, verbose=False):
        """ Display execution results """
        status = result["status"]

        if status == "SUCCESS":
            print("Execution Status: SUCCESS")
        else:
            print("Execution Status: FAILED")
            if result.get("error"):
                print(f"  Error: {result['error']}")

        print(f"Duration: {result['duration_seconds']:.2f}s")
        print()

        # Display context variables
        context = result.get("context", {})
        if context:
            print("Results:")
            print("-" * 70)
            for key, value in context.items():
                if key == "inputs":
                    continue
                if isinstance(value, dict) and len(str(value)) > 100:
                    print(f"  {key}: [complex object]")
                else:
                    print(f"  {key}: {value}")
            print()

        # Show execution log if verbose
        if verbose and result.get("execution_log"):
            print("Execution Log:")
            print("-" * 70)
            for entry in result["execution_log"]:
                timestamp = entry["timestamp"].split('T')[1].split('.')[0]
                level = entry["level"]
                message = entry["message"]
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