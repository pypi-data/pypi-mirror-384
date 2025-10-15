"""Tests for the argparser module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from steputil import StepArgsBuilder, InputField, OutputField


def test_input_field_read_jsonls():
    """Test reading JSONL file with InputField."""
    # Create a temporary JSONL file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        temp_path = f.name
        f.write('{"id": 1, "name": "Alice"}\n')
        f.write('{"id": 2, "name": "Bob"}\n')
        f.write('{"id": 3, "name": "Charlie"}\n')

    try:
        input_field = InputField(temp_path)
        result = input_field.readJsons()

        assert len(result) == 3
        assert result[0] == {"id": 1, "name": "Alice"}
        assert result[1] == {"id": 2, "name": "Bob"}
        assert result[2] == {"id": 3, "name": "Charlie"}
    finally:
        Path(temp_path).unlink()


def test_input_field_read_jsonls_with_empty_lines():
    """Test reading JSONL file with empty lines."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        temp_path = f.name
        f.write('{"id": 1}\n')
        f.write("\n")
        f.write('{"id": 2}\n')
        f.write("  \n")
        f.write('{"id": 3}\n')

    try:
        input_field = InputField(temp_path)
        result = input_field.readJsons()

        assert len(result) == 3
        assert result[0] == {"id": 1}
        assert result[1] == {"id": 2}
        assert result[2] == {"id": 3}
    finally:
        Path(temp_path).unlink()


def test_output_field_write_jsonls():
    """Test writing JSONL file with OutputField."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output.jsonl"
        output_field = OutputField(str(output_path))

        data = [
            {"id": 1, "value": "first"},
            {"id": 2, "value": "second"},
            {"id": 3, "value": "third"},
        ]

        output_field.writeJsons(data)

        # Read back and verify
        with open(output_path, "r") as f:
            lines = f.readlines()

        assert len(lines) == 3
        assert json.loads(lines[0]) == {"id": 1, "value": "first"}
        assert json.loads(lines[1]) == {"id": 2, "value": "second"}
        assert json.loads(lines[2]) == {"id": 3, "value": "third"}


def test_output_field_creates_parent_directory():
    """Test that OutputField creates parent directories if needed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "subdir" / "nested" / "output.jsonl"
        output_field = OutputField(str(output_path))

        data = [{"test": "value"}]
        output_field.writeJsons(data)

        assert output_path.exists()
        with open(output_path, "r") as f:
            result = json.loads(f.readline())
        assert result == {"test": "value"}


def test_builder_single_input_output():
    """Test builder with single default input and output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.jsonl"
        output_path = Path(tmpdir) / "output.jsonl"

        # Create input file
        with open(input_path, "w") as f:
            f.write('{"data": "test"}\n')

        # Mock command line arguments
        test_args = ["--input", str(input_path), "--output", str(output_path)]

        with patch("sys.argv", ["test_script.py"] + test_args):
            args = StepArgsBuilder().input().output().build()

            # Test input field
            assert hasattr(args, "input")
            assert isinstance(args.input, InputField)
            assert args.input.path == str(input_path)

            data = args.input.readJsons()
            assert data == [{"data": "test"}]

            # Test output field
            assert hasattr(args, "output")
            assert isinstance(args.output, OutputField)
            assert args.output.path == str(output_path)

            args.output.writeJsons([{"result": "success"}])

            with open(output_path, "r") as f:
                result = json.loads(f.readline())
            assert result == {"result": "success"}


def test_builder_multiple_inputs_outputs():
    """Test builder with multiple named inputs and outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input1_path = Path(tmpdir) / "input1.jsonl"
        input2_path = Path(tmpdir) / "input2.jsonl"
        output1_path = Path(tmpdir) / "output1.jsonl"
        output2_path = Path(tmpdir) / "output2.jsonl"

        # Create input files
        with open(input1_path, "w") as f:
            f.write('{"source": 1}\n')
        with open(input2_path, "w") as f:
            f.write('{"source": 2}\n')

        test_args = [
            "--data-source",
            str(input1_path),
            "--config-file",
            str(input2_path),
            "--result-file",
            str(output1_path),
            "--log-file",
            str(output2_path),
        ]

        with patch("sys.argv", ["test_script.py"] + test_args):
            args = (
                StepArgsBuilder()
                .input("data_source")
                .input("config_file")
                .output("result_file")
                .output("log_file")
                .build()
            )

            # Test inputs
            assert hasattr(args, "data_source")
            assert hasattr(args, "config_file")
            assert args.data_source.readJsons() == [{"source": 1}]
            assert args.config_file.readJsons() == [{"source": 2}]

            # Test outputs
            assert hasattr(args, "result_file")
            assert hasattr(args, "log_file")

            args.result_file.writeJsons([{"output": 1}])
            args.log_file.writeJsons([{"log": "entry"}])

            with open(output1_path, "r") as f:
                assert json.loads(f.readline()) == {"output": 1}
            with open(output2_path, "r") as f:
                assert json.loads(f.readline()) == {"log": "entry"}


def test_builder_no_inputs_or_outputs():
    """Test builder with no inputs or outputs."""
    with patch("sys.argv", ["test_script.py"]):
        args = StepArgsBuilder().build()
        # Should create empty args object without errors
        assert args is not None


def test_builder_chaining():
    """Test that builder methods return self for chaining."""
    builder = StepArgsBuilder()
    assert builder.input() is builder
    assert builder.output() is builder
    assert builder.config("test_field") is builder


def test_config_required_field():
    """Test config with required field."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        input_path = Path(tmpdir) / "input.jsonl"

        # Create config file
        with open(config_path, "w") as f:
            json.dump({"api_key": "secret123"}, f)

        # Create input file
        with open(input_path, "w") as f:
            f.write('{"data": "test"}\n')

        test_args = ["--input", str(input_path), "--config", str(config_path)]

        with patch("sys.argv", ["test_script.py"] + test_args):
            args = StepArgsBuilder().input().config("api_key").build()

            assert hasattr(args, "config")
            assert hasattr(args.config, "api_key")
            assert args.config.api_key == "secret123"


def test_config_optional_field_with_value():
    """Test optional config field with value provided."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        input_path = Path(tmpdir) / "input.jsonl"

        with open(config_path, "w") as f:
            json.dump({"timeout": 30}, f)

        with open(input_path, "w") as f:
            f.write('{"data": "test"}\n')

        test_args = ["--input", str(input_path), "--config", str(config_path)]

        with patch("sys.argv", ["test_script.py"] + test_args):
            args = StepArgsBuilder().input().config("timeout", optional=True).build()

            assert args.config.timeout == 30


def test_config_optional_field_without_value():
    """Test optional config field without value (should be None)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        input_path = Path(tmpdir) / "input.jsonl"

        with open(config_path, "w") as f:
            json.dump({}, f)

        with open(input_path, "w") as f:
            f.write('{"data": "test"}\n')

        test_args = ["--input", str(input_path), "--config", str(config_path)]

        with patch("sys.argv", ["test_script.py"] + test_args):
            args = StepArgsBuilder().input().config("timeout", optional=True).build()

            assert args.config.timeout is None


def test_config_default_value():
    """Test config field with default value."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        input_path = Path(tmpdir) / "input.jsonl"

        with open(config_path, "w") as f:
            json.dump({}, f)

        with open(input_path, "w") as f:
            f.write('{"data": "test"}\n')

        test_args = ["--input", str(input_path), "--config", str(config_path)]

        with patch("sys.argv", ["test_script.py"] + test_args):
            args = StepArgsBuilder().input().config("timeout", default_value=60).build()

            assert args.config.timeout == 60


def test_config_value_overrides_default():
    """Test that config file value overrides default."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        input_path = Path(tmpdir) / "input.jsonl"

        with open(config_path, "w") as f:
            json.dump({"timeout": 30}, f)

        with open(input_path, "w") as f:
            f.write('{"data": "test"}\n')

        test_args = ["--input", str(input_path), "--config", str(config_path)]

        with patch("sys.argv", ["test_script.py"] + test_args):
            args = StepArgsBuilder().input().config("timeout", default_value=60).build()

            assert args.config.timeout == 30


def test_config_missing_required_field():
    """Test that missing required field raises ValueError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        input_path = Path(tmpdir) / "input.jsonl"

        with open(config_path, "w") as f:
            json.dump({}, f)

        with open(input_path, "w") as f:
            f.write('{"data": "test"}\n')

        test_args = ["--input", str(input_path), "--config", str(config_path)]

        with patch("sys.argv", ["test_script.py"] + test_args):
            with pytest.raises(ValueError, match="Required configuration field"):
                StepArgsBuilder().input().config("api_key").build()


def test_config_multiple_fields():
    """Test config with multiple fields of different types."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        input_path = Path(tmpdir) / "input.jsonl"

        config_data = {
            "api_key": "secret123",
            "timeout": 30,
            "max_retries": 3,
        }

        with open(config_path, "w") as f:
            json.dump(config_data, f)

        with open(input_path, "w") as f:
            f.write('{"data": "test"}\n')

        test_args = ["--input", str(input_path), "--config", str(config_path)]

        with patch("sys.argv", ["test_script.py"] + test_args):
            args = (
                StepArgsBuilder()
                .input()
                .config("api_key")
                .config("timeout", default_value=60)
                .config("max_retries", optional=True)
                .config("debug", optional=True, default_value=False)
                .build()
            )

            assert args.config.api_key == "secret123"
            assert args.config.timeout == 30
            assert args.config.max_retries == 3
            assert args.config.debug is False


def test_validate_success():
    """Test validation callback that returns True."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        input_path = Path(tmpdir) / "input.jsonl"

        with open(config_path, "w") as f:
            json.dump({"timeout": 30}, f)

        with open(input_path, "w") as f:
            f.write('{"data": "test"}\n')

        test_args = ["--input", str(input_path), "--config", str(config_path)]

        def validate_timeout(config):
            return config.timeout > 0

        with patch("sys.argv", ["test_script.py"] + test_args):
            args = (
                StepArgsBuilder()
                .input()
                .config("timeout")
                .validate(validate_timeout)
                .build()
            )

            assert args.config.timeout == 30


def test_validate_failure():
    """Test validation callback that returns False."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        input_path = Path(tmpdir) / "input.jsonl"

        with open(config_path, "w") as f:
            json.dump({"timeout": -10}, f)

        with open(input_path, "w") as f:
            f.write('{"data": "test"}\n')

        test_args = ["--input", str(input_path), "--config", str(config_path)]

        def validate_timeout(config):
            return config.timeout > 0

        with patch("sys.argv", ["test_script.py"] + test_args):
            with pytest.raises(ValueError, match="Configuration validation failed"):
                (
                    StepArgsBuilder()
                    .input()
                    .config("timeout")
                    .validate(validate_timeout)
                    .build()
                )


def test_validate_complex_rules():
    """Test validation with complex rules checking multiple fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        input_path = Path(tmpdir) / "input.jsonl"

        config_data = {"min_value": 10, "max_value": 100}

        with open(config_path, "w") as f:
            json.dump(config_data, f)

        with open(input_path, "w") as f:
            f.write('{"data": "test"}\n')

        test_args = ["--input", str(input_path), "--config", str(config_path)]

        def validate_range(config):
            return config.min_value < config.max_value

        with patch("sys.argv", ["test_script.py"] + test_args):
            args = (
                StepArgsBuilder()
                .input()
                .config("min_value")
                .config("max_value")
                .validate(validate_range)
                .build()
            )

            assert args.config.min_value == 10
            assert args.config.max_value == 100


def test_validate_complex_rules_failure():
    """Test validation failure with complex rules."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        input_path = Path(tmpdir) / "input.jsonl"

        config_data = {"min_value": 100, "max_value": 10}

        with open(config_path, "w") as f:
            json.dump(config_data, f)

        with open(input_path, "w") as f:
            f.write('{"data": "test"}\n')

        test_args = ["--input", str(input_path), "--config", str(config_path)]

        def validate_range(config):
            return config.min_value < config.max_value

        with patch("sys.argv", ["test_script.py"] + test_args):
            with pytest.raises(ValueError, match="Configuration validation failed"):
                (
                    StepArgsBuilder()
                    .input()
                    .config("min_value")
                    .config("max_value")
                    .validate(validate_range)
                    .build()
                )
