import argparse
import shutil
from pathlib import Path
from typing import List, Optional

from .sync_module import SyncModule

from .base_module import BaseModule
from ..config import Config
from ..error_handler import ValidationError, logger
from ...api import ScoutAPI


class AssistantsModule(BaseModule):
    def __init__(self, config: Config) -> None:
        self.config = config

    def get_command(self) -> str:
        return "assistants"

    def add_parser(self, subparsers: argparse._SubParsersAction) -> None:
        assistants_parser = subparsers.add_parser(
            self.get_command(), help="Manage assistants"
        )

        # Create subparsers for assistants commands
        assistants_subparsers = assistants_parser.add_subparsers(
            dest="assistants_command", required=True
        )

        # assistants init
        init_parser = assistants_subparsers.add_parser(
            "init", help="Create an assistant.json from template"
        )
        init_parser.add_argument(
            "-d",
            "--directory",
            type=str,
            default=".",
            help="Directory to create the assistant files in (default: current directory)",
        )
        init_parser.set_defaults(func=self._init_assistant)

        # assistants list
        list_parser = assistants_subparsers.add_parser(
            "list", help="List all assistants"
        )
        list_parser.set_defaults(func=self._list_assistants)

        # assistants synchronize
        sync_parser = assistants_subparsers.add_parser(
            "synchronize", help="Synchronize assistants from config file"
        )
        sync_parser.add_argument(
            "-f", "--file", type=str, required=True, help="Path to assistants.json file"
        )
        sync_parser.add_argument(
            "--force", action="store_true", help="Force overwrite assistant files"
        )
        sync_parser.add_argument(
            "-o",
            "--overwrite",
            action="store_true",
            help="Overwrite the config file with new assistant IDs (useful for first-time creation)",
        )
        sync_parser.set_defaults(func=self._synchronize_assistants)

    def execute(self, args: argparse.Namespace) -> None:
        """Execute the assistants command."""
        # This will be called by the specific subcommand
        args.func(args)

    def _init_assistant(self, args: argparse.Namespace) -> None:
        """Initialize a new assistant.json from template."""
        # First step: Choose template type
        print("\nChoose an assistant template:")
        print("1. basic - Basic assistant template")
        print("2. assistant with function - Assistant template with custom function")
        print("3. assistant with micro-app - Assistant template with micro-app")
        print(
            "4. assistant with micro-app and function - Assistant with both micro-app and custom function"
        )

        choice = input("Enter your choice (1-4): ").strip()

        if choice not in ["1", "2", "3", "4", ""]:  # Allow empty for default
            raise ValidationError("Invalid choice. Please select 1, 2, 3, or 4.")

        # Default to basic if empty
        if not choice:
            choice = "1"

        # Second step: Get assistant name
        assistant_name = input("\nEnter assistant name: ").strip()
        if not assistant_name:
            raise ValidationError("Assistant name cannot be empty")

        # Create target directory if it doesn't exist
        target_dir = Path(args.directory)
        target_dir.mkdir(exist_ok=True)

        if choice == "1":
            # Basic assistant template
            self._create_basic_assistant(assistant_name, target_dir)
        elif choice == "2":
            # Assistant with function template
            self._create_assistant_with_functions(assistant_name, target_dir)
        elif choice == "3":
            # Assistant with micro-app template
            self._create_assistant_with_micro_app(assistant_name, target_dir)
        else:  # choice == "4"
            # Assistant with micro-app and function template
            self._create_assistant_with_micro_app_and_function(
                assistant_name, target_dir
            )

    def _create_basic_assistant(self, assistant_name: str, target_dir: Path) -> None:
        """Create a basic assistant template."""
        # Load template
        template_path = (
            Path(__file__).parent.parent.parent
            / "data"
            / "assistants"
            / "basic"
            / "assistants_template.json"
        )
        if not template_path.exists():
            raise ValidationError("Basic assistant template file not found")

        with open(template_path, "r") as f:
            content = f.read()

        # Replace placeholders in the template
        assistant_id = assistant_name.lower().replace(" ", "_").replace("-", "_")
        content = content.replace("{ASSISTANT_NAME}", assistant_name)
        content = content.replace("{ASSISTANT_IDENTIFIER}", assistant_id)

        # Write to target directory as assistants.json
        output_file = target_dir / "assistants.json"
        with open(output_file, "w") as f:
            f.write(content)

        # Copy supporting template files to target directory
        self._copy_assistant_template_files(target_dir)

        logger.info(
            f"Created basic assistant '{assistant_name}' with config file '{output_file}'"
        )

    def _create_assistant_with_micro_app(
        self, assistant_name: str, target_dir: Path
    ) -> None:
        """Create an assistant template with micro-app."""
        # Use AppsModule to create the micro-app
        from .apps_module import AppsModule

        apps_module = AppsModule(self.config)
        micro_app_type = apps_module.create_micro_app_for_assistant(target_dir)

        # Create assistant template with micro-app configuration
        self._create_micro_app_assistant_template(assistant_name, target_dir)

        logger.info(
            f"Created assistant '{assistant_name}' with {micro_app_type} micro-app in '{target_dir}'"
        )

    def _create_assistant_with_functions(
        self, assistant_name: str, target_dir: Path
    ) -> None:
        """Create an assistant template with functions."""
        # Create functions directory
        functions_dir = target_dir / "functions"
        functions_dir.mkdir(exist_ok=True)

        # Create the function using the functions module logic (will ask for template type and name)
        created_function_name = self._create_function_for_assistant(functions_dir)

        # Create assistant template with function integration
        self._create_assistant_template_with_functions(
            assistant_name, target_dir, created_function_name
        )

        logger.info(
            f"Created assistant '{assistant_name}' with function '{created_function_name}' in '{target_dir}'"
        )

    def _create_function_for_assistant(self, functions_dir: Path) -> str:
        """Create a function for the assistant (reusing function creation logic)."""
        # Import the functions module to reuse its logic
        from .functions_module import FunctionsModule
        import argparse
        import builtins

        # Create a mock args object for the functions module
        mock_args = argparse.Namespace()
        mock_args.directory = str(functions_dir)

        # Create functions module instance
        functions_module = FunctionsModule(self.config)

        # Track the function name that gets created
        created_function_name: List[Optional[str]] = [
            None
        ]  # Use list to make it mutable
        original_input = builtins.input

        def capture_input(prompt: str) -> str:
            result = original_input(prompt)
            # Capture function name when it's entered
            if any(
                keyword in prompt.lower()
                for keyword in [
                    "function name",
                    "document chunker name",
                    "webhook name",
                ]
            ):
                # Normalize the name like the functions module does
                created_function_name[0] = functions_module._normalize_function_name(
                    result
                )
            return result

        try:
            # Override input to capture the function name
            builtins.input = capture_input  # type: ignore[assignment]

            # Use the existing _init_function method - this will handle template choice and name prompts in correct order
            functions_module._init_function(mock_args)

        finally:
            # Restore original input function
            builtins.input = original_input

        # Return the normalized function name that was created
        return created_function_name[0] or "unknown_function"

    def _create_assistant_with_micro_app_and_function(
        self, assistant_name: str, target_dir: Path
    ) -> None:
        """Create an assistant template with both micro-app and custom function."""
        # Create functions directory
        functions_dir = target_dir / "functions"
        functions_dir.mkdir(exist_ok=True)

        # Create the function using the functions module logic (will ask for template type and name)
        created_function_name = self._create_function_for_assistant(functions_dir)

        # Use AppsModule to create the micro-app
        from .apps_module import AppsModule

        apps_module = AppsModule(self.config)
        micro_app_type = apps_module.create_micro_app_for_assistant(target_dir)

        # Create assistant template with both micro-app and function configuration
        self._create_assistant_template_with_micro_app_and_function(
            assistant_name, target_dir, created_function_name
        )

        logger.info(
            f"Created assistant '{assistant_name}' with function '{created_function_name}' and {micro_app_type} micro-app in '{target_dir}'"
        )

    def _create_assistant_template_with_functions(
        self, assistant_name: str, target_dir: Path, function_name: str
    ) -> None:
        """Create assistant template that includes function configuration."""
        assistant_id = assistant_name.lower().replace(" ", "_").replace("-", "_")

        template_path = (
            Path(__file__).parent.parent.parent
            / "data"
            / "assistants"
            / "with-function"
            / "assistants_template.json"
        )
        if not template_path.exists():
            raise ValidationError("Advanced assistant template file not found")

        with open(template_path, "r") as f:
            template_content = f.read()

        # Replace placeholders in the template
        assistant_id = assistant_name.lower().replace(" ", "_").replace("-", "_")
        template_content = template_content.replace("{ASSISTANT_NAME}", assistant_name)
        template_content = template_content.replace(
            "{ASSISTANT_IDENTIFIER}", assistant_id
        )
        template_content = template_content.replace("{FUNCTION_NAME}", function_name)

        # Write to target directory as assistants.json
        output_file = target_dir / "assistants.json"
        with open(output_file, "w") as f:
            f.write(template_content)

        # Copy avatar file
        self._copy_assistant_template_files(target_dir)

    def _normalize_function_name(self, name: str) -> str:
        """Normalize function name to lowercase with underscores."""
        import re

        # Convert to lowercase and replace spaces and special characters with underscores
        normalized = re.sub(r"[^\w\s]", "_", name.lower())
        normalized = re.sub(r"\s+", "_", normalized)
        # Remove multiple consecutive underscores
        normalized = re.sub(r"_+", "_", normalized)
        # Remove leading/trailing underscores
        normalized = normalized.strip("_")
        return normalized or "custom_function"

    def _copy_assistant_template_files(self, target_dir: Path) -> None:
        """Copy supporting template files to target directory."""
        # Define source and destination paths
        assistants_data_path = (
            Path(__file__).parent.parent.parent
            / "data"
            / "assistants"
            / "with-function"
        )

        # For basic template, only copy avatar.jpeg
        avatar_src = assistants_data_path / "avatar.jpeg"
        avatar_dest = target_dir / "avatar.jpeg"

        if avatar_src.exists() and not avatar_dest.exists():
            shutil.copy2(avatar_src, avatar_dest)
        else:
            logger.warning(f"Avatar template file not found: {avatar_src}")

    def _list_assistants(self, args: argparse.Namespace) -> None:
        """List all assistants."""
        try:
            scout_api = ScoutAPI()
            assistants = scout_api.assistants.list_all()

            if not assistants:
                logger.info("No assistants found")
                return

            logger.info(f"Found {len(assistants)} assistants:")
            for assistant in assistants:
                logger.info(f"  - {assistant.name} (ID: {assistant.id})")

        except Exception as e:
            raise ValidationError(f"Failed to list assistants: {str(e)}")

    def _synchronize_assistants(self, args: argparse.Namespace) -> None:
        """Synchronize assistants from config file."""
        # Import and use existing sync functionality
        from .pkg_module import PkgModule

        pkg_module = PkgModule(config=self.config)
        sync_module = SyncModule(config=self.config, pkg_module=pkg_module)

        # Create args compatible with existing sync module
        sync_args = argparse.Namespace()
        sync_args.config = args.file
        sync_args.force = getattr(args, "force", False)

        sync_module.execute(sync_args)

    def _create_micro_app_assistant_template(
        self, assistant_name: str, target_dir: Path
    ) -> None:
        """Create assistant template with micro-app configuration."""
        # Load micro-app assistant template
        template_path = (
            Path(__file__).parent.parent.parent
            / "data"
            / "assistants"
            / "with-micro-app"
            / "assistants_template.json"
        )
        if not template_path.exists():
            raise ValidationError("Micro-app assistant template file not found")

        with open(template_path, "r") as f:
            content = f.read()

        # Replace placeholders in the template
        assistant_id = assistant_name.lower().replace(" ", "_").replace("-", "_")
        content = content.replace("{ASSISTANT_NAME}", assistant_name)
        content = content.replace("{ASSISTANT_IDENTIFIER}", assistant_id)

        # Write to target directory as assistants.json
        output_file = target_dir / "assistants.json"
        with open(output_file, "w") as f:
            f.write(content)

        # Copy avatar and supporting files
        self._copy_assistant_template_files(target_dir)

    def _create_assistant_template_with_micro_app_and_function(
        self, assistant_name: str, target_dir: Path, function_name: str
    ) -> None:
        """Create assistant template with both micro-app and function."""
        # Load the with-micro-app-and-function template
        template_path = (
            Path(__file__).parent.parent.parent
            / "data"
            / "assistants"
            / "with-micro-app-and-function"
            / "assistants_template.json"
        )
        if not template_path.exists():
            raise ValidationError(
                "Assistant template with micro-app and function not found"
            )

        with open(template_path, "r") as f:
            content = f.read()

        # Replace placeholders in the template
        assistant_id = assistant_name.lower().replace(" ", "_").replace("-", "_")
        content = content.replace("{ASSISTANT_NAME}", assistant_name)
        content = content.replace("{ASSISTANT_IDENTIFIER}", assistant_id)
        content = content.replace("{FUNCTION_NAME}", function_name)

        # Write to target directory as assistants.json
        output_file = target_dir / "assistants.json"
        with open(output_file, "w") as f:
            f.write(content)

        # Copy avatar and supporting files
        self._copy_assistant_template_files(target_dir)
