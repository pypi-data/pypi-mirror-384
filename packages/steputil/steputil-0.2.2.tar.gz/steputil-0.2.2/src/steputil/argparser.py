"""Command-line argument parser with builder pattern for pipeline steps."""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional


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


class StepArgs:
    """Container for parsed command-line arguments with input/output fields."""

    def __init__(
        self, args_dict: Dict[str, str], input_names: List[str], output_names: List[str]
    ):
        """Initialize StepArgs with parsed arguments.

        Args:
            args_dict: Dictionary of argument name to value.
            input_names: List of input field names.
            output_names: List of output field names.
        """
        # Create InputField objects for each input
        for name in input_names:
            setattr(self, name, InputField(args_dict[name]))

        # Create OutputField objects for each output
        for name in output_names:
            setattr(self, name, OutputField(args_dict[name]))


class StepArgsBuilder:
    """Builder for creating command-line argument parser with input/output fields."""

    def __init__(self):
        """Initialize the builder."""
        self._inputs: List[tuple[str, Optional[str]]] = []
        self._outputs: List[tuple[str, Optional[str]]] = []

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

    def build(self) -> StepArgs:
        """Build the argument parser and parse command-line arguments.

        Returns:
            StepArgs object with parsed input/output fields.
        """
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

        # Parse arguments
        args = parser.parse_args()
        args_dict = vars(args)

        # Convert dashes back to underscores for field names
        normalized_dict = {k.replace("-", "_"): v for k, v in args_dict.items()}

        input_names = [name for name, _ in self._inputs]
        output_names = [name for name, _ in self._outputs]

        return StepArgs(normalized_dict, input_names, output_names)
