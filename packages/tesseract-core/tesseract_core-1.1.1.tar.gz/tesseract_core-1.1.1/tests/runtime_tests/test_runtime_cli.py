# Copyright 2025 Pasteur Labs. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import copy
import json
import os
import subprocess
import sys
import traceback
from copy import deepcopy
from pathlib import Path

import boto3
import fsspec
import numpy as np
import pytest
from moto.server import ThreadedMotoServer
from typer.testing import CliRunner

from tesseract_core.runtime.cli import _add_user_commands_to_cli
from tesseract_core.runtime.cli import app as cli_cmd
from tesseract_core.runtime.file_interactions import output_to_bytes

test_input = {
    "a": [1.0, 2.0, 3.0],
    "b": [1, 1, 1],
    "s": 2.5,
}
test_input_binref = {
    "a": {
        "object_type": "array",
        "shape": [3],
        "dtype": "float64",
        "data": {
            "buffer": "data.bin",
            "encoding": "binref",
        },
    },
    "b": {
        "object_type": "array",
        "shape": [3],
        "dtype": "int64",
        "data": {
            "buffer": "data.bin:24",
            "encoding": "binref",
        },
    },
    "s": test_input["s"],
}


@pytest.fixture(autouse=True)
def use_dummy_tesseract(dummy_tesseract):
    yield


@pytest.fixture
def cli_runner():
    return CliRunner(mix_stderr=False)


@pytest.fixture(scope="module")
def test_s3_server():
    """Fixture to run a mocked AWS server for testing."""
    current_conf = copy.deepcopy(fsspec.config.conf)

    server = ThreadedMotoServer(port=0)
    server.start()

    os.environ.update(
        AWS_ACCESS_KEY_ID="dummy-access-key",
        AWS_SECRET_ACCESS_KEY="dummy-access-key-secret",
        AWS_DEFAULT_REGION="us-east-1",
    )

    try:
        host, port = server.get_host_and_port()

        moto_server = f"http://{host}:{port}"

        client = boto3.client("s3", endpoint_url=moto_server)
        client.create_bucket(Bucket="test-bucket")

        client.put_object(
            Bucket="test-bucket",
            Key="foo.json",
            Body=json.dumps({"inputs": test_input}),
        )

        for array in ("a", "b"):
            client.put_object(
                Bucket="test-bucket",
                Key=f"array_{array}.bin",
                Body=np.asarray(test_input[array]).tobytes(),
            )

        fsspec.config.conf["s3"] = dict(endpoint_url=moto_server)
        yield "s3://test-bucket"
    finally:
        server.stop()
        fsspec.config.conf = current_conf
        os.environ.pop("AWS_ACCESS_KEY_ID")
        os.environ.pop("AWS_SECRET_ACCESS_KEY")
        os.environ.pop("AWS_DEFAULT_REGION")


@pytest.fixture()
def test_http_server(free_port):
    """Start a local HTTP server for testing that always returns `test_input`."""
    import http.server
    import socketserver
    import threading

    import requests

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if "/foo.json" == self.path:
                bytes = json.dumps({"inputs": test_input}).encode("utf-8")
            elif "/array_a.bin" == self.path:
                bytes = np.asarray(test_input["a"]).tobytes()
            elif "/array_b.bin" == self.path:
                bytes = np.asarray(test_input["b"]).tobytes()
            else:
                raise ValueError(f"No such file {self.path}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(bytes)

    httpd = socketserver.TCPServer(("", free_port), Handler)

    def run_server():
        httpd.serve_forever()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    try:
        # wait for server to start
        while True:
            res = requests.get(f"http://localhost:{free_port}/foo.json")
            if res.status_code == 200:
                break

        yield f"http://localhost:{free_port}"
    finally:
        httpd.shutdown()
        server_thread.join()


@pytest.fixture
def cli():
    new_cmd = copy.deepcopy(cli_cmd)
    _add_user_commands_to_cli(new_cmd, out_stream=None)
    return new_cmd


def test_invocation_no_args_prints_usage(cli, cli_runner):
    result = cli_runner.invoke(cli, env={"TERM": "dumb"})
    assert result.exit_code == 0, result.stdout
    assert "Usage: tesseract-runtime" in result.stdout


def test_openapi_schema_command(cli, cli_runner):
    result = cli_runner.invoke(cli, ["openapi-schema"])
    assert result.exit_code == 0, result.stderr
    assert '"openapi":' in result.stdout


def test_abstract_eval_command(cli, cli_runner):
    input_shape = {"dtype": "float32", "shape": [4]}
    result = cli_runner.invoke(
        cli,
        [
            "abstract-eval",
            json.dumps({"inputs": {"a": input_shape, "b": input_shape}}),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr
    json_out = json.loads(result.stdout)
    assert {"result": {"shape": [4], "dtype": "float32"}} == json_out


def test_apply_command(cli, cli_runner, dummy_tesseract_module):
    inputs = dummy_tesseract_module.InputSchema(**test_input).model_dump_json(
        context={"array_encoding": "base64"}
    )
    inputs = json.loads(inputs)
    inputs = {"inputs": inputs}
    result = cli_runner.invoke(
        cli,
        ["apply", json.dumps(inputs)],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr
    test_input_val = dummy_tesseract_module.InputSchema.model_validate(test_input)
    expected = dummy_tesseract_module.apply(test_input_val).model_dump_json()
    assert json.loads(result.stdout) == json.loads(expected)


def test_apply_command_binref(cli, cli_runner, dummy_tesseract_module, tmpdir):
    # construct payload with absolute paths
    test_input_absolute = deepcopy(test_input_binref)
    test_input_absolute["a"]["data"]["buffer"] = str(tmpdir / "data.bin")
    test_input_absolute["b"]["data"]["buffer"] = str(tmpdir / "data.bin:24")

    # write array to current tempdir so that we can read from here
    with open(tmpdir / "data.bin", "wb") as fi:
        fi.write(np.asarray(test_input["a"]).tobytes())
        fi.write(np.asarray(test_input["b"]).tobytes())

    result = cli_runner.invoke(
        cli,
        ["apply", json.dumps({"inputs": test_input_absolute})],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr
    test_input_val = dummy_tesseract_module.InputSchema.model_validate(test_input)
    expected = dummy_tesseract_module.apply(test_input_val).model_dump_json()
    assert json.loads(result.stdout) == json.loads(expected)

    result = cli_runner.invoke(
        cli,
        ["apply", json.dumps({"inputs": test_input_binref})],
        catch_exceptions=False,
        env={"TERM": "dumb", "COLUMNS": "1000"},
    )
    assert result.exit_code == 2
    assert "Value error" in result.stderr
    assert "Failed to decode buffer as binref" in result.stderr


def test_apply_command_noenv(cli, cli_runner, dummy_tesseract_module, monkeypatch):
    monkeypatch.delenv("TESSERACT_API_PATH", raising=False)
    assert "TESSERACT_API_PATH" not in os.environ
    inputs = dummy_tesseract_module.InputSchema(**test_input).model_dump_json(
        context={"array_encoding": "base64"}
    )
    inputs = json.loads(inputs)
    inputs = {"inputs": inputs}
    result = cli_runner.invoke(
        cli,
        ["apply", json.dumps(inputs)],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr
    test_input_val = dummy_tesseract_module.InputSchema.model_validate(test_input)
    expected = dummy_tesseract_module.apply(test_input_val).model_dump_json()
    assert json.loads(result.stdout) == json.loads(expected)


@pytest.mark.parametrize("input_format", ["json", "json+base64", "json+binref"])
def test_input_vals_from_local_file(
    cli, cli_runner, tmpdir, dummy_tesseract_module, input_format
):
    """Test the apply command with input arguments from a local file."""
    container = input_format.split("+")[-1]

    a_file = tmpdir / f"a.{container}"
    inputs = {"inputs": dummy_tesseract_module.InputSchema(**test_input)}
    input_bytes = output_to_bytes(inputs, input_format, base_dir=Path(tmpdir))

    if input_format == "json+binref":
        # Make sure a binref file is created
        assert list(Path(tmpdir).glob("*.bin")) != []

    with open(a_file, "wb") as f:
        f.write(input_bytes)

    result = cli_runner.invoke(
        cli,
        ["--input-path", tmpdir, "apply", f"@{a_file}"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr

    result = result.stdout

    test_input_val = dummy_tesseract_module.InputSchema.model_validate(test_input)
    expected = dummy_tesseract_module.apply(test_input_val).model_dump_json()
    assert json.loads(result) == json.loads(expected)


@pytest.mark.parametrize("output_format", ["json", "json+base64", "json+binref"])
def test_outputs_to_local_file(
    cli, cli_runner, tmpdir, dummy_tesseract_module, output_format
):
    """Test the apply command writing outputs to a local file."""
    tmpdir = Path(tmpdir)
    container = output_format.split("+")[0]
    result = cli_runner.invoke(
        cli,
        [
            "--output-path",
            tmpdir,
            "--output-format",
            output_format,
            "--output-file",
            f"results.{container}",
            "apply",
            json.dumps({"inputs": test_input}),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr

    test_input_val = dummy_tesseract_module.InputSchema.model_validate(test_input)

    load_bytes = lambda x, fmt: json.loads(x.decode("utf-8"))

    expected = dummy_tesseract_module.apply(test_input_val)
    expected = output_to_bytes(expected, output_format, base_dir=tmpdir)
    expected = load_bytes(expected, output_format)

    outfile = tmpdir / f"results.{container}"

    with open(outfile, "rb") as f:
        result = load_bytes(f.read(), output_format)

    def _replace_binref_paths(obj):
        # Replace binref paths with a placeholder so they can be compared
        if isinstance(obj, dict):
            if (
                obj.get("object_type") == "array"
                and obj["data"]["encoding"] == "binref"
            ):
                obj["data"]["buffer"] = "path/to/binref.bin"
                return obj
            return {k: _replace_binref_paths(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_replace_binref_paths(x) for x in obj]
        return obj

    expected = _replace_binref_paths(expected)
    result = _replace_binref_paths(result)

    if container == "json":
        assert result == expected
    else:
        # Unreachable
        raise AssertionError(f"Unexpected output format: {output_format}")


@pytest.mark.parametrize(
    "test_server",
    [
        "test_s3_server",
        "test_http_server",
    ],
)
def test_input_vals_from_network(
    cli, cli_runner, dummy_tesseract_module, test_server, request
):
    """Test the apply command with input arguments from a remote JSON file."""
    server_path = request.getfixturevalue(test_server)

    result = cli_runner.invoke(
        cli,
        ["apply", f"@{server_path}/foo.json"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr

    test_input_val = dummy_tesseract_module.InputSchema.model_validate(test_input)
    expected = dummy_tesseract_module.apply(test_input_val).model_dump_json()
    assert json.loads(result.stdout) == json.loads(expected)


@pytest.mark.parametrize(
    "test_server",
    [
        "test_s3_server",
        "test_http_server",
    ],
)
def test_input_vals_from_network_binref(
    cli, cli_runner, dummy_tesseract_module, test_server, request
):
    """Test the apply command with input arguments from a remote JSON file."""
    server_path = request.getfixturevalue(test_server)

    # construct payload with networks paths
    test_input_network = deepcopy(test_input_binref)
    test_input_network["a"]["data"]["buffer"] = f"{server_path}/array_a.bin"
    test_input_network["b"]["data"]["buffer"] = f"{server_path}/array_b.bin"

    result = cli_runner.invoke(
        cli,
        ["apply", json.dumps({"inputs": test_input_network})],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr

    test_input_val = dummy_tesseract_module.InputSchema.model_validate(test_input)
    expected = dummy_tesseract_module.apply(test_input_val).model_dump_json()
    assert json.loads(result.stdout) == json.loads(expected)


def test_help_contains_docstring(cli, cli_runner):
    summary = "Multiplies a vector `a` by `s`, and sums the result to `b`."
    result = cli_runner.invoke(cli, ["apply", "--help"], catch_exceptions=False)
    assert result.exit_code == 0, result.stderr
    assert summary in result.stdout


def test_optional_arguments_stay_optional_in_cli(
    cli, cli_runner, dummy_tesseract_module
):
    test_input_missing = {"a": [1.0, 2.0, 3.0], "b": [1, 1, 1]}
    result = cli_runner.invoke(
        cli,
        [
            "apply",
            json.dumps({"inputs": test_input_missing}),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr

    test_input_val = dummy_tesseract_module.InputSchema.model_validate(
        test_input_missing
    )
    expected = dummy_tesseract_module.apply(test_input_val).model_dump_json()
    assert json.loads(result.stdout) == json.loads(expected)


def test_apply_fails_if_required_args_missing(cli, cli_runner):
    result = cli_runner.invoke(cli, ["apply", json.dumps({"inputs": {"a": [1, 2, 3]}})])
    assert result.exit_code == 2
    assert "missing" in result.stderr


def test_stdout_redirect_cli():
    """Ensure that stdout is redirected to stderr during normal Python execution."""
    import tesseract_core.runtime.cli

    # Use subprocess to ensure that CLI entrypoint is used
    result = subprocess.run(
        [sys.executable, tesseract_core.runtime.cli.__file__, "--help"],
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == b""
    assert "Usage:" in result.stderr.decode("utf-8")


@pytest.mark.parametrize("target", ["file", "stderr"])
def test_stdout_redirect_subprocess(tmpdir, target):
    """Ensure that stdout is redirected to stderr / files even in non-Python subprocesses."""
    if target == "file":
        target_stream = "f"
    else:
        target_stream = "sys.stderr"

    testscript = [
        # Print messages that signify where the output is supposed to go
        "import os",
        "import sys",
        "from tesseract_core.runtime.core import redirect_fd",
        "print('stdout', file=sys.stdout)",
        "print('stderr', file=sys.stderr)",
        f"with open(\"{tmpdir / 'test_output.log'}\", 'w') as f:",
        f"  with redirect_fd(sys.stdout, {target_stream}) as orig_stdout:",
        "    os.system('echo stderr')",
        "    print('stderr', file=sys.stdout)",
        "    print('stderr', file=sys.stderr)",
        "    print('stdout', file=orig_stdout)",
        "os.system('echo stdout')",
        "print('stdout', file=sys.stdout)",
        "print('stderr', file=sys.stderr)",
    ]
    testscript_path = tmpdir / "testscript.py"
    with open(testscript_path, "w") as f:
        f.write("\n".join(testscript))

    # Use subprocess since pytest messes with stdout/stderr
    result = subprocess.run([sys.executable, testscript_path], capture_output=True)
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert result.stdout == b"stdout\n" * 4

    if target == "file":
        assert result.stderr == b"stderr\n" * 3
        # Find the log file
        log_file = tmpdir / "test_output.log"
        with open(log_file, "rb") as f:
            log_content = f.read()
        assert log_content == b"stderr\n" * 2
    else:
        assert result.stderr == b"stderr\n" * 5


def test_suggestion_on_misspelled_command(cli, cli_runner):
    result = cli_runner.invoke(cli, ["aply"], catch_exceptions=False)
    assert result.exit_code == 2, result.stdout
    assert "No such command 'aply'." in result.stderr
    assert "Did you mean 'apply'?" in result.stderr

    result = cli_runner.invoke(cli, ["applecomputersinc"], catch_exceptions=False)
    assert result.exit_code == 2, result.stdout
    assert "No such command 'applecomputersinc'." in result.stderr
    assert "Did you mean" not in result.stderr


def test_check(cli, cli_runner, dummy_tesseract_package):
    from tesseract_core.runtime.config import update_config

    tesseract_api_file = Path(dummy_tesseract_package) / "tesseract_api.py"
    update_config(api_path=tesseract_api_file)
    result = cli_runner.invoke(cli, ["check"], catch_exceptions=True)
    assert result.exit_code == 0, result.stderr
    assert "check successful" in result.stdout

    api_file_bad_syntax = Path(dummy_tesseract_package) / "tesseract_api_bad_syntax.py"
    with open(api_file_bad_syntax, "w") as f:
        f.write("bad-syntax=1")

    update_config(api_path=api_file_bad_syntax)
    result = cli_runner.invoke(cli, ["check"], catch_exceptions=True)
    assert result.exit_code == 1, result.stderr
    assert "Could not load module" in result.exception.args[0]
    full_traceback = "".join(traceback.format_exception(*result.exc_info))
    assert "SyntaxError" in full_traceback

    # Write new file for each case instead of overwriting same file to avoid caching issues
    api_file_bad_import = Path(dummy_tesseract_package) / "tesseract_api_bad_import.py"
    with open(api_file_bad_import, "w") as f:
        f.write("import non_existent_module")

    update_config(api_path=api_file_bad_import)
    result = cli_runner.invoke(cli, ["check"], catch_exceptions=True)
    assert result.exit_code == 1, result.stderr
    assert "Could not load module" in result.exception.args[0]
    full_traceback = "".join(traceback.format_exception(*result.exc_info))
    assert "ModuleNotFoundError" in full_traceback

    with open(tesseract_api_file) as f:
        tesseract_api_code = f.read()

    # check if error is raised if schemas or required endpoints are missing
    for schema_or_endpoint in ("InputSchema", "OutputSchema", "apply"):
        invalid_code = tesseract_api_code.replace(
            f"{schema_or_endpoint}", f"{schema_or_endpoint}_hide"
        )
        api_file_missing_schema_or_endpoint = (
            Path(dummy_tesseract_package)
            / f"tesseract_api_missing_{schema_or_endpoint.lower()}.py"
        )
        with open(api_file_missing_schema_or_endpoint, "w") as f:
            f.write(invalid_code)
        update_config(api_path=api_file_missing_schema_or_endpoint)
        result = cli_runner.invoke(cli, ["check"], catch_exceptions=True)
        assert result.exit_code == 1, result.stderr
        full_traceback = "".join(traceback.format_exception(*result.exc_info))
        assert (
            f"{schema_or_endpoint} is not defined in Tesseract API module"
            in result.exception.args[0]
        )

    # check if error is raised for schemas with unsupported parent class
    for schema_name in ("InputSchema", "OutputSchema"):
        invalid_code = tesseract_api_code.replace(
            f"{schema_name}(BaseModel)", f"{schema_name}(tuple)"
        )
        api_file_bad_parent_class = (
            Path(dummy_tesseract_package)
            / f"tesseract_api_bad_{schema_name.lower()}_parent_class.py"
        )
        with open(api_file_bad_parent_class, "w") as f:
            f.write(invalid_code)
        update_config(api_path=api_file_bad_parent_class)
        result = cli_runner.invoke(cli, ["check"], catch_exceptions=True)
        assert result.exit_code == 1, result.stderr
        full_traceback = "".join(traceback.format_exception(*result.exc_info))
        assert (
            f"{schema_name} is not a subclass of pydantic.BaseModel"
            in result.exception.args[0]
        )
