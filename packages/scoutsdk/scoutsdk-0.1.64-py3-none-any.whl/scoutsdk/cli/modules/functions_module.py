import argparse
import shutil
import re
from pathlib import Path

from .base_module import BaseModule
from ..config import Config
from ..error_handler import ValidationError, logger
from ...api import ScoutAPI


class FunctionsModule(BaseModule):
    def __init__(self, config: Config) -> None:
        self.config = config

    def get_command(self) -> str:
        return "functions"

    def add_parser(self, subparsers: argparse._SubParsersAction) -> None:
        functions_parser = subparsers.add_parser(
            self.get_command(), help="Manage functions"
        )

        # Create subparsers for functions commands
        functions_subparsers = functions_parser.add_subparsers(
            dest="functions_command", required=True
        )

        # functions init
        init_parser = functions_subparsers.add_parser(
            "init", help="Initialize a new function"
        )
        init_parser.add_argument(
            "-d",
            "--directory",
            type=str,
            default="functions",
            help="Directory to create the function in (default: functions)",
        )
        init_parser.set_defaults(func=self._init_function)

        # functions package
        package_parser = functions_subparsers.add_parser(
            "package", help="Package functions for deployment"
        )
        package_parser.add_argument(
            "path",
            nargs="?",
            default=".",
            help="Path to functions directory (default: current directory)",
        )
        package_parser.add_argument("-o", "--output", help="Output package filename")
        package_parser.set_defaults(func=self._package_functions)

        # functions deploy
        deploy_parser = functions_subparsers.add_parser(
            "deploy", help="Deploy functions to assistant"
        )
        deploy_parser.add_argument(
            "-a", "--assistant-id", required=True, help="Assistant ID to deploy to"
        )
        deploy_parser.add_argument(
            "path",
            nargs="?",
            default=".",
            help="Path to functions directory (default: current directory)",
        )
        deploy_parser.set_defaults(func=self._deploy_functions)

    def execute(self, args: argparse.Namespace) -> None:
        """Execute the functions command."""
        args.func(args)

    def _init_function(self, args: argparse.Namespace) -> None:
        """Initialize a new function from template."""
        # First step: Choose template type
        print("\nChoose a function template:")
        print("1. scout function - Pre-built Scout function template")
        print("2. scout document chunker - Document processing template")
        print("3. webhook - Create a webhook endpoint")

        choice = input("Enter your choice (1-3): ").strip()

        if choice not in ["1", "2", "3"]:
            raise ValidationError("Invalid choice. Please select 1, 2, or 3.")

        # Second step: Get name based on template choice
        if choice == "1":
            raw_function_name = input("\nEnter function name: ").strip()
            if not raw_function_name:
                raise ValidationError("Function name cannot be empty")
        elif choice == "2":
            raw_function_name = input("Enter document chunker name: ").strip()
            if not raw_function_name:
                raise ValidationError("Document chunker name cannot be empty")
        else:  # choice == "3"
            raw_function_name = input("Enter webhook name: ").strip()
            if not raw_function_name:
                raise ValidationError("Webhook name cannot be empty")

        # Normalize function name: lowercase, replace spaces/special chars with underscores
        function_name = self._normalize_function_name(raw_function_name)

        if function_name != raw_function_name:
            logger.info(f"Name normalized to: {function_name}")

        # Create base directory if it doesn't exist
        base_dir = Path(args.directory)
        base_dir.mkdir(exist_ok=True)

        # Create the function file directly in the base directory
        function_file = base_dir / f"{function_name}.py"

        if function_file.exists():
            raise ValidationError(f"Function file '{function_file}' already exists")

        # Copy template files to base directory if they don't exist
        template_source = Path(__file__).parent.parent.parent / "data" / "functions"

        # Copy essential files to base directory if not present
        essential_files = ["__init__.py", "requirements.txt", ".pkgignore"]
        for file in essential_files:
            src = template_source / file
            dest = base_dir / file
            if src.exists() and not dest.exists():
                shutil.copy2(src, dest)

        # Create the function file based on template choice
        if choice == "1":
            self._create_scout_function(function_file, function_name, template_source)
        elif choice == "2":
            self._create_document_chunker_function(
                function_file, function_name, template_source
            )
        elif choice == "3":
            self._create_webhook_function(function_file, function_name, template_source)

        # Log creation message based on template type
        if choice == "1":
            logger.info(
                f"Created scout function '{function_name}' at '{function_file}'"
            )
        elif choice == "2":
            class_name = self._to_camel_case(function_name) + "Chunker"
            logger.info(f"Created document chunker '{class_name}' at '{function_file}'")
        else:  # choice == "3"
            logger.info(
                f"Created webhook '{function_name}' at '{function_file}'.\n Once deployed in an assistants, the webhook endpoint (POST) will be http://your_instance.scout.com/api/assistants/{{assistants_id}}/webhooks/{function_name}"
            )

    def _normalize_function_name(self, name: str) -> str:
        """Normalize function name to lowercase with underscores."""
        # Convert to lowercase and replace spaces and special characters with underscores
        normalized = re.sub(r"[^\w\s]", "_", name.lower())
        normalized = re.sub(r"\s+", "_", normalized)
        # Remove multiple consecutive underscores
        normalized = re.sub(r"_+", "_", normalized)
        # Remove leading/trailing underscores
        normalized = normalized.strip("_")
        return normalized or "custom_function"

    def _to_camel_case(self, name: str) -> str:
        """Convert function name to CamelCase for class names."""
        # Split by underscores and capitalize each part
        parts = name.split("_")
        return "".join(word.capitalize() for word in parts if word)

    def _create_scout_function(
        self, function_file: Path, function_name: str, template_source: Path
    ) -> None:
        """Create a scout function from the existing template."""
        src_template = template_source / "function_template.py"
        if not src_template.exists():
            raise ValidationError("Scout function template file not found")
            return

        with open(src_template, "r") as f:
            content = f.read()

        # Replace the function name in the template
        content = content.replace("this_is_a_test_function", function_name)

        # Add the if __name__ == "__main__" block if not present
        if 'if __name__ == "__main__"' not in content:
            # Create a proper call with example parameters for the scout function template
            content += f"""


if __name__ == "__main__":
    {function_name}(my_parameter="hello world")
"""

        with open(function_file, "w") as f:
            f.write(content)

    def _create_document_chunker_function(
        self, function_file: Path, function_name: str, template_source: Path
    ) -> None:
        """Create a document chunker function from template."""
        src_template = template_source / "document_chunker_template.py"
        if not src_template.exists():
            raise ValidationError("Document chunker template file not found")
            return

        with open(src_template, "r") as f:
            content = f.read()

        # Convert function name to CamelCase for class name
        class_name = self._to_camel_case(function_name)

        # Replace the class name in the template
        content = content.replace("DemoChunker", class_name)

        # Add the if __name__ == "__main__" block
        content += f"""


if __name__ == "__main__":
    # Create chunker instance and test
    chunker = {class_name}()
    result = chunker.process_document("test_url")
    print(result)
"""

        with open(function_file, "w") as f:
            f.write(content)

    def _create_webhook_function(
        self, function_file: Path, function_name: str, template_source: Path
    ) -> None:
        """Create a webhook function from template."""
        src_template = template_source / "webhook_template.py"
        if not src_template.exists():
            raise ValidationError("Webhook template file not found")
            return

        with open(src_template, "r") as f:
            content = f.read()

        # Replace the function name in the template
        content = content.replace("my_webhook", function_name)

        # Add the if __name__ == "__main__" block
        content += f"""


if __name__ == "__main__":
    {function_name}()
"""

        with open(function_file, "w") as f:
            f.write(content)

    def _package_functions(self, args: argparse.Namespace) -> None:
        """Package functions for deployment."""
        from .pkg_module import PkgModule

        pkg_module = PkgModule(config=self.config)

        # Determine output filename
        path = Path(args.path)
        if args.output:
            output_filename = args.output
        else:
            output_filename = f"{path.name}_functions.zip"

        try:
            pkg_module.generate_package(str(path), output_filename)
            logger.info(f"Functions packaged successfully: {output_filename}")
        except Exception as e:
            raise ValidationError(f"Failed to package functions: {str(e)}")

    def _deploy_functions(self, args: argparse.Namespace) -> None:
        """Deploy packaged functions to an assistant."""
        # First package the functions
        path = Path(args.path)
        package_filename = f"{path.name}_functions.zip"

        self._package_functions(
            argparse.Namespace(path=args.path, output=package_filename)
        )

        try:
            scout_api = ScoutAPI()

            # Upload the package file to the assistant
            from scouttypes.assistants.file_types import FileType

            scout_api.assistants.upload_file(
                assistant_id=args.assistant_id,
                file_path=package_filename,
                file_type=FileType.CUSTOM_FUNCTIONS,
            )

            logger.info(
                f"Functions deployed successfully to assistant {args.assistant_id}"
            )

            # Clean up the temporary package file
            Path(package_filename).unlink(missing_ok=True)

        except Exception as e:
            # Clean up on failure
            Path(package_filename).unlink(missing_ok=True)
            raise ValidationError(f"Failed to deploy functions: {str(e)}")
