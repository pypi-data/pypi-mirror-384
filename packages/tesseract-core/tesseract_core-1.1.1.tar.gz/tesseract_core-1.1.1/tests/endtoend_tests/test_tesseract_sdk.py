# Copyright 2025 Pasteur Labs. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import inspect
import socket

import numpy as np
import pytest
from common import build_tesseract, image_exists

from tesseract_core import Tesseract
from tesseract_core.sdk import engine

expected_endpoints = {
    "apply",
    "jacobian",
    "health",
    "abstract_eval",
    "jacobian_vector_product",
    "vector_jacobian_product",
}


@pytest.fixture(scope="module")
def built_image_name(
    docker_client,
    shared_dummy_image_name,
    dummy_tesseract_location,
    docker_cleanup_module,
):
    """Build the dummy Tesseract image for the tests."""
    image_name = build_tesseract(
        docker_client, dummy_tesseract_location, shared_dummy_image_name
    )
    assert image_exists(docker_client, image_name)
    docker_cleanup_module["images"].append(image_name)
    yield image_name


def test_available_endpoints(built_image_name):
    with Tesseract.from_image(built_image_name) as vecadd:
        assert set(vecadd.available_endpoints) == expected_endpoints


def test_apply(built_image_name, dummy_tesseract_location, free_port):
    inputs = {"a": [1, 2], "b": [3, 4], "s": 1}

    # Test URL access
    tesseract_url = f"http://localhost:{free_port}"
    served_tesseract, _ = engine.serve(built_image_name, port=str(free_port))
    try:
        vecadd = Tesseract(tesseract_url)
        out = vecadd.apply(inputs)
    finally:
        engine.teardown(served_tesseract)

    assert set(out.keys()) == {"result"}
    np.testing.assert_array_equal(out["result"], np.array([4.0, 6.0]))

    # Test from_image (context manager)
    with Tesseract.from_image(built_image_name) as vecadd:
        out = vecadd.apply(inputs)

    assert set(out.keys()) == {"result"}
    np.testing.assert_array_equal(out["result"], np.array([4.0, 6.0]))

    # Test from_image (serve + teardown)
    vecadd = Tesseract.from_image(built_image_name)
    try:
        vecadd.serve()
        out = vecadd.apply(inputs)
    finally:
        vecadd.teardown()

    assert set(out.keys()) == {"result"}
    np.testing.assert_array_equal(out["result"], np.array([4.0, 6.0]))

    # Test from_tesseract_api
    with Tesseract.from_tesseract_api(
        dummy_tesseract_location / "tesseract_api.py"
    ) as vecadd:
        out = vecadd.apply(inputs)

    assert set(out.keys()) == {"result"}
    np.testing.assert_array_equal(out["result"], np.array([4.0, 6.0]))


def test_apply_with_error(built_image_name):
    # pass two inputs with different shapes, which raises an internal error
    inputs = {"a": [1, 2, 3], "b": [3, 4], "s": 1}

    with Tesseract.from_image(built_image_name) as vecadd:
        with pytest.raises(RuntimeError) as excinfo:
            vecadd.apply(inputs)

    assert "assert a.shape == b.shape" in str(excinfo.value)

    # get logs
    logs = vecadd.server_logs()
    assert "assert a.shape == b.shape" in logs


@pytest.fixture(scope="module")
def served_tesseract_remote(built_image_name):
    # Find a free port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("", 0))
    free_port = sock.getsockname()[1]
    sock.close()
    # Serve the Tesseract image
    tesseract_url = f"http://localhost:{free_port}"
    served_tesseract, _ = engine.serve(built_image_name, port=str(free_port))
    try:
        yield tesseract_url
    finally:
        engine.teardown(served_tesseract)


@pytest.fixture(scope="module")
def served_tesseract_from_image(built_image_name):
    with Tesseract.from_image(built_image_name) as vecadd:
        yield vecadd


@pytest.fixture(scope="module")
def served_tesseract_module(dummy_tesseract_location):
    vecadd = Tesseract.from_tesseract_api(dummy_tesseract_location / "tesseract_api.py")
    yield vecadd


@pytest.mark.parametrize(
    "endpoint_name", sorted(expected_endpoints | {"openapi_schema"})
)
def test_all_endpoints(
    endpoint_name,
    served_tesseract_module,
    served_tesseract_from_image,
    served_tesseract_remote,
):
    """Test that all endpoints can be invoked without errors."""
    inputs = {"a": [1, 2], "b": [3, 4], "s": 1}

    if endpoint_name == "apply":
        inputs = {"inputs": inputs}
    elif endpoint_name == "jacobian":
        inputs = {"inputs": inputs, "jac_inputs": ["a"], "jac_outputs": ["result"]}
    elif endpoint_name == "jacobian_vector_product":
        inputs = {
            "inputs": inputs,
            "jvp_inputs": ["a"],
            "jvp_outputs": ["result"],
            "tangent_vector": {"a": np.array([1.0, 1.0])},
        }
    elif endpoint_name == "vector_jacobian_product":
        inputs = {
            "inputs": inputs,
            "vjp_inputs": ["a"],
            "vjp_outputs": ["result"],
            "cotangent_vector": {"result": np.array([1.0, 1.0])},
        }
    elif endpoint_name == "abstract_eval":
        inputs = {
            "abstract_inputs": {
                "a": {"shape": [2], "dtype": "float32"},
                "b": {"shape": [2], "dtype": "float32"},
            }
        }
    else:
        inputs = {}

    # Test from_tesseract_api
    out = getattr(served_tesseract_module, endpoint_name)
    if callable(out):
        out(**inputs)

    # Test from_image
    out = getattr(served_tesseract_from_image, endpoint_name)
    if callable(out):
        out(**inputs)

    # Test URL access
    vecadd = Tesseract(served_tesseract_remote)
    out = getattr(vecadd, endpoint_name)
    if callable(out):
        out(**inputs)


def test_signature_consistency():
    """Test that from_image and engine.serve have the same signature."""
    allowed_diff = [
        # debug mode is always enabled in from_image
        "debug",
        # setting output format is not meaningful (arrays are decoded automatically)
        "output_format",
    ]

    from_image_sig = dict(inspect.signature(Tesseract.from_image).parameters)
    serve_sig = dict(inspect.signature(engine.serve).parameters)

    for param in allowed_diff:
        from_image_sig.pop(param, None)
        serve_sig.pop(param, None)

    assert set(from_image_sig.keys()) == set(serve_sig.keys())

    for key in from_image_sig:
        assert from_image_sig[key].default == serve_sig[key].default, (
            f"Default value mismatch for parameter '{key}': "
            f"{from_image_sig[key].default} != {serve_sig[key].default}"
        )


def test_logpipe_consistency():
    """Test that the source code of the two duplicate LogPipe implementations is identical."""
    from tesseract_core.runtime.logs import LogPipe as RuntimeLogPipe
    from tesseract_core.sdk.logs import LogPipe as SDKLogPipe

    runtime_source = inspect.getsource(RuntimeLogPipe)
    sdk_source = inspect.getsource(SDKLogPipe)
    assert runtime_source == sdk_source
