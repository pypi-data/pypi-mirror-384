"""Command-line argument parser with builder pattern for pipeline steps."""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable


class InputField:
    """Represents an input file field with JSONL reading capability."""

    def __init__(self, path: str):
        """Initialize an input field with a file path.

        Args:
            path: Path to the input file.
        """
        self.path = path

    def readJsons(self) -> List[Dict[str, Any]]:
        """Read JSONL file and return list of JSON objects.

        Returns:
            List of dictionaries representing JSON objects from the file.

        Raises:
            FileNotFoundError: If the input file doesn't exist.
            json.JSONDecodeError: If a line contains invalid JSON.
        """
        result = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:  # Skip empty lines
                    try:
                        result.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        raise json.JSONDecodeError(
                            f"Invalid JSON on line {line_num}: {e.msg}", e.doc, e.pos
                        )
        return result


class OutputField:
    """Represents an output file field with JSONL writing capability."""

    def __init__(self, path: str):
        """Initialize an output field with a file path.

        Args:
            path: Path to the output file.
        """
        self.path = path

    def writeJsons(self, jsons: List[Dict[str, Any]]) -> None:
        """Write list of JSON objects to JSONL file.

        Args:
            jsons: List of dictionaries to write as JSON lines.
        """
        # Create parent directory if it doesn't exist
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)

        with open(self.path, "w", encoding="utf-8") as f:
            for obj in jsons:
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")


class Config:
    """Container for configuration values."""

    pass


class StepArgs:
    """Container for parsed command-line arguments with input/output fields."""

    def __init__(
        self,
        args_dict: Dict[str, str],
        input_names: List[str],
        output_names: List[str],
        config_obj: Optional[Config] = None,
    ):
        """Initialize StepArgs with parsed arguments.

        Args:
            args_dict: Dictionary of argument name to value.
            input_names: List of input field names.
            output_names: List of output field names.
            config_obj: Optional Config object with configuration values.
        """
        # Create InputField objects for each input
        for name in input_names:
            setattr(self, name, InputField(args_dict[name]))

        # Create OutputField objects for each output
        for name in output_names:
            setattr(self, name, OutputField(args_dict[name]))

        # Set config object if provided
        if config_obj is not None:
            self.config = config_obj


class _Sentinel:
    """Sentinel value to distinguish between None and unset default values."""

    pass


_UNSET = _Sentinel()


class StepArgsBuilder:
    """Builder for creating command-line argument parser with input/output fields."""

    def __init__(self):
        """Initialize the builder."""
        self._inputs: List[tuple[str, Optional[str]]] = []
        self._outputs: List[tuple[str, Optional[str]]] = []
        self._configs: List[tuple[str, bool, Any]] = []  # (name, optional, default)
        self._validation_callback: Optional[Callable[[Config], bool]] = None

    def input(self, name: Optional[str] = None) -> "StepArgsBuilder":
        """Add an input field to the argument parser.

        Args:
            name: Name of the input parameter. If None, uses 'input'.

        Returns:
            Self for method chaining.
        """
        field_name = name if name is not None else "input"
        self._inputs.append((field_name, name))
        return self

    def output(self, name: Optional[str] = None) -> "StepArgsBuilder":
        """Add an output field to the argument parser.

        Args:
            name: Name of the output parameter. If None, uses 'output'.

        Returns:
            Self for method chaining.
        """
        field_name = name if name is not None else "output"
        self._outputs.append((field_name, name))
        return self

    def config(
        self,
        name: str,
        optional: bool = False,
        default_value: Any = _UNSET,
    ) -> "StepArgsBuilder":
        """Add a configuration field.

        Args:
            name: Name of the configuration field (required).
            optional: Whether the field is optional. Defaults to False.
            default_value: Default value if not set in config file.

        Returns:
            Self for method chaining.
        """
        self._configs.append((name, optional, default_value))
        return self

    def validate(self, callback: Callable[[Config], bool]) -> "StepArgsBuilder":
        """Add a validation callback for configuration.

        Args:
            callback: Function that takes Config object and returns True if valid.

        Returns:
            Self for method chaining.
        """
        self._validation_callback = callback
        return self

    def build(self) -> StepArgs:
        """Build the argument parser and parse command-line arguments.

        If no command-line arguments are provided and inputs/outputs are defined,
        prints the contents of /app/README.md and exits.

        Returns:
            StepArgs object with parsed input/output fields.

        Raises:
            ValueError: If a required config field is missing or invalid.
        """
        # Check if command line is empty and we have inputs/outputs defined
        if len(sys.argv) == 1 and (self._inputs or self._outputs):
            readme_path = Path("/app/README.md")
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    print(f.read())
            except FileNotFoundError:
                print(f"README.md not found at {readme_path}", file=sys.stderr)
            sys.exit(0)

        parser = argparse.ArgumentParser(
            description="Pipeline step with configurable inputs and outputs"
        )

        # Add input arguments
        for field_name, original_name in self._inputs:
            arg_name = f'--{field_name.replace("_", "-")}'
            parser.add_argument(
                arg_name,
                type=str,
                required=True,
                help=f"Path to input file for {field_name}",
            )

        # Add output arguments
        for field_name, original_name in self._outputs:
            arg_name = f'--{field_name.replace("_", "-")}'
            parser.add_argument(
                arg_name,
                type=str,
                required=True,
                help=f"Path to output file for {field_name}",
            )

        # Add config argument if configs are defined
        if self._configs:
            parser.add_argument(
                "--config",
                type=str,
                required=True,
                help="Path to configuration JSON file",
            )

        # Parse arguments
        args = parser.parse_args()
        args_dict = vars(args)

        # Convert dashes back to underscores for field names
        normalized_dict = {k.replace("-", "_"): v for k, v in args_dict.items()}

        input_names = [name for name, _ in self._inputs]
        output_names = [name for name, _ in self._outputs]

        # Process config if defined
        config_obj = None
        if self._configs:
            config_path = normalized_dict.pop("config")
            config_data = self._load_config_file(config_path)
            config_obj = self._create_config_object(config_data)

            # Validate config if validation callback is provided
            if self._validation_callback is not None:
                if not self._validation_callback(config_obj):
                    raise ValueError("Configuration validation failed")

        return StepArgs(normalized_dict, input_names, output_names, config_obj)

    def _load_config_file(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file.

        Args:
            config_path: Path to the configuration JSON file.

        Returns:
            Dictionary containing configuration data.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            json.JSONDecodeError: If config file contains invalid JSON.
        """
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Config file must contain a JSON object")
            return data

    def _create_config_object(self, config_data: Dict[str, Any]) -> Config:
        """Create Config object from configuration data.

        Args:
            config_data: Dictionary containing configuration values.

        Returns:
            Config object with fields set according to config specifications.

        Raises:
            ValueError: If a required field is missing.
        """
        config_obj = Config()

        for name, optional, default_value in self._configs:
            if name in config_data:
                # Value exists in config file
                value = config_data[name]
            elif default_value is not _UNSET:
                # Use default value
                value = default_value
            elif optional:
                # Optional field without default
                value = None
            else:
                # Required field is missing
                raise ValueError(
                    f"Required configuration field '{name}' is missing "
                    f"from config file"
                )

            setattr(config_obj, name, value)

        return config_obj
