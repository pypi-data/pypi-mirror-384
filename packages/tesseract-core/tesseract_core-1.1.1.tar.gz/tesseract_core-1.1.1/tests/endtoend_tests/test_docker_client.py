# Copyright 2025 Pasteur Labs. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""End to end tests for docker cli wrapper."""

import os
import subprocess
from contextlib import closing
from pathlib import Path

import docker
import pytest
from common import image_exists

from tesseract_core.sdk.docker_client import (
    ContainerError,
    ImageNotFound,
    _is_valid_docker_tag,
    build_docker_image,
    is_podman,
)


@pytest.fixture(scope="module")
def docker_py_client():
    # Create a Docker client using the docker-py library
    # You may need to set the environment variable $DOCKER_HOST if encountering issues
    with closing(docker.from_env()) as client:
        yield client


@pytest.fixture()
def docker_client_built_image_name(
    docker_client,
    dummy_tesseract_location,
    dummy_docker_file,
):
    """Build the dummy image for the tests."""
    image_names = [
        f"docker_client_create_image_test:{tag}" for tag in ["dummy", "latest"]
    ]

    build_docker_image(dummy_tesseract_location, image_names, dummy_docker_file)
    try:
        # Let's just return one tag to use in tests, even if we are
        # creating multiple ones for testing purposes.
        yield image_names[0]
    finally:
        for image in image_names:
            try:
                docker_client.images.remove(image)
            except ImageNotFound:
                # already removed
                pass


def test_get_image(docker_client, docker_client_built_image_name, docker_py_client):
    """Test image retrieval."""

    def _strip_image_prefix(image_name):
        """Strip the 'sha256:' prefix from the image name if it exists."""
        if image_name.startswith("sha256:"):
            return image_name.split(":")[1]
        return image_name

    # Get the image
    image = docker_client.images.get(docker_client_built_image_name)
    assert image is not None

    docker_py_image = docker_py_client.images.get(docker_client_built_image_name)
    assert docker_py_image is not None

    docker_image_short = docker_client.images.get(image.short_id)
    assert docker_image_short == image

    # Whether images start with sha256: depends on the used Docker implementation (e.g. Podman vs. Docker)
    if docker_py_image.short_id.startswith("sha256:"):
        non_sha_id = docker_py_image.short_id.split(":")[1]
        docker_image_non_sha = docker_client.images.get(non_sha_id)
        assert docker_image_non_sha is not None
        assert docker_image_short.id == docker_image_non_sha.id

    assert _strip_image_prefix(image.id) == _strip_image_prefix(docker_py_image.id)
    assert _strip_image_prefix(image.short_id) == _strip_image_prefix(
        docker_py_image.short_id
    )
    assert image.tags == docker_py_image.tags
    # Check the repr function
    assert (
        str(image)
        == f"Image(id='{image.id}', short_id='{image.short_id}', tags={image.tags}, attrs={image.attrs})"
    )

    # Check that every image listed by docker cli can be found
    # Dangling images are not listed by the client
    image_ids = subprocess.run(
        [
            "docker",
            "images",
            "--filter",
            "dangling=false",
            "-q",
        ],  # List only image IDs
        capture_output=True,
        text=True,
        check=True,
    )
    image_ids = image_ids.stdout.strip().split("\n")
    # Filter list to exclude empty strings.
    image_ids = [image_id for image_id in image_ids if image_id]
    for image_id in image_ids:
        assert image_exists(docker_client, image_id, tesseract_only=False)

    image_list = docker_client.images.list(tesseract_only=False)
    assert image_list is not None
    assert len(image_list) > 0

    docker_py_image_list = docker_py_client.images.list()
    assert docker_py_image_list is not None

    # Check that every image in image_list is also in docker_py_image_list
    docker_py_image_ids = set(
        _strip_image_prefix(img.id) for img in docker_py_image_list if img
    )
    for image in image_list:
        assert _strip_image_prefix(image.id) in docker_py_image_ids


def test_create_image(
    docker_client,
    docker_py_client,
    dummy_tesseract_location,
    dummy_docker_file,
    docker_client_built_image_name,
):
    """Test image building, getting, and removing.

    Validate image existence in both docker_py_client and docker_client to ensure
    handling of names/ids are the same.
    """
    image1, image2 = None, None
    # Create an image
    try:
        image = docker_client.images.get(docker_client_built_image_name)
        assert image is not None

        image_id_obj = docker_client.images.get(image.id)
        image_short_id_obj = docker_client.images.get(image.short_id)
        assert image == image_id_obj
        assert image_short_id_obj == image
        assert image_exists(docker_client, docker_client_built_image_name)
        assert image_exists(docker_py_client, docker_client_built_image_name)

        # Create a second image with no label
        # Check that :latest gets added automatically
        image1_name = "docker_client_create_image_test:latest"
        docker_client.images.buildx(
            dummy_tesseract_location, [image1_name], dummy_docker_file
        )
        image1 = docker_client.images.get(image1_name)
        assert image1 is not None
        assert image_exists(docker_client, image1_name)
        assert image_exists(docker_py_client, image1_name)

        # Create a third image with prefixed with repo url
        # Check that name gets handled properly
        repo_url = "local_host/foo/bar/"
        image2_name = "docker_client_create_image_url_test:latest"
        docker_client.images.buildx(
            dummy_tesseract_location, [repo_url + image2_name], dummy_docker_file
        )
        image2_py = docker_py_client.images.get(repo_url + image2_name)
        assert image2_py is not None

        image2 = docker_client.images.get(repo_url + image2_name)
        assert image2 is not None

    finally:
        # Clean up the images
        if image1:
            docker_client.images.remove(image1_name)
            assert not image_exists(docker_client, image1_name)
            assert not image_exists(docker_py_client, image1_name)

        if image2:
            docker_client.images.remove(repo_url + image2_name)
            assert not image_exists(docker_client, image2_name)
            assert not image_exists(docker_py_client, repo_url + image2_name)


def test_create_container(
    docker_client, docker_py_client, docker_client_built_image_name
):
    """Test container creation, run, logs, and remove."""

    def _strip_image_prefix(image_name):
        """Strip the 'sha256:' prefix from the image name if it exists."""
        if image_name.startswith("sha256:"):
            return image_name.split(":")[1]
        return image_name

    # Create a container
    container, container_py = None, None
    try:
        container = docker_client.containers.run(
            docker_client_built_image_name, ['echo "Hello, Tesseract!"'], detach=True
        )
        assert container is not None
        container_py = docker_py_client.containers.run(
            docker_client_built_image_name, ['echo "Hello, Tesseract!"'], detach=True
        )
        assert container_py is not None
        # Check property fields
        assert container.host_port is None
        assert _strip_image_prefix(container_py.image.id) == _strip_image_prefix(
            container.image.id
        )

        container_get = docker_client.containers.get(container.id)
        container_name_get = docker_client.containers.get(container.name)
        container_py_get = docker_py_client.containers.get(container.id)
        container_py_name_get = docker_py_client.containers.get(container.name)
        assert container_get
        assert container_name_get
        assert container_py_get
        assert container_py_name_get

        assert container_name_get == container_get
        # Only compare the key fields of the original container and the ones from get
        # in case container attrs have been updated since creation
        assert container.id == container_get.id
        assert container.name == container_get.name
        # Compare the docker-py container fields vs docker client fields
        assert container_get.id == container_py_get.id
        assert container_get.short_id == container_py_get.short_id
        assert container_get.name == container_py_get.name
        assert container_get.id == container_py_name_get.id

        status = container.wait()
        status_py = container_py.wait()
        assert status["StatusCode"] == 0
        assert status_py["StatusCode"] == 0

        stdout = container.logs(stdout=True, stderr=False)
        stderr = container.logs(stdout=False, stderr=True)
        assert stdout == b"Hello, Tesseract!\n"
        assert stderr == b""

        stdout_py = container_py.logs(stdout=True, stderr=False)
        stderr_py = container_py.logs(stdout=False, stderr=True)
        assert stdout_py == stdout
        assert stderr_py == stderr

    finally:
        # Clean up the container
        if container:
            container.remove(v=True, force=True)
            # Check that the container is removed
            containers = docker_client.containers.list()
            containers_py = docker_py_client.containers.list()
            assert container.id not in containers
            assert container.id not in containers_py

        if container_py:
            container_py.remove(v=True, force=True)
            # Check that the container is removed
            containers = docker_client.containers.list()
            containers_py = docker_py_client.containers.list()
            assert container_py.id not in containers
            assert container_py.id not in containers_py


def test_container_volume_mounts(
    docker_client, docker_cleanup, docker_client_built_image_name, tmp_path
):
    """Test container volume mounts."""
    container1 = None
    # Pytest creates the tmp_path fixture with drwx------ mode, we need others
    # to be able to read and execute the path so the Docker volume is readable
    # from within the container
    tmp_path.chmod(0o0707)

    dest = Path("/foo/")
    bar_file = dest / "hello.txt"
    stdout = docker_client.containers.run(
        docker_client_built_image_name,
        [f"touch {bar_file} && chmod 777 {bar_file} && echo hello"],
        detach=False,
        volumes={tmp_path: {"bind": dest, "mode": "rw"}},
        remove=True,
    )

    assert stdout == b"hello\n"
    # Check file exists in tmp path
    assert (tmp_path / "hello.txt").exists()

    # Check container is removed and there are no running containers associated with the test image
    result = subprocess.run(
        [
            "docker",
            "ps",
            "--filter",
            f"ancestor={docker_client_built_image_name}",
            "-q",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout == ""

    # Open tmp_path/hello.txt in write mode
    with open(tmp_path / "hello.txt", "w") as f:
        f.write("hello tesseract\n")

    # Check we can read it in another container
    container1 = docker_client.containers.run(
        docker_client_built_image_name,
        [f"cat {dest}/hello.txt"],
        detach=True,
        volumes={tmp_path: {"bind": dest, "mode": "rw"}},
    )
    docker_cleanup["containers"].append(container1)
    status = container1.wait()
    assert status["StatusCode"] == 0
    stdout = container1.logs(stdout=True, stderr=False)
    assert stdout == b"hello tesseract\n"


def test_volume_uid_permissions(
    docker_client, docker_client_built_image_name, docker_volume, docker_cleanup
):
    # Set up root only directory
    def run_tesseract_with_volume(cmd: str, user: str = "root:root", volume: str = ""):
        if not volume:
            volume = {docker_volume.name: {"bind": "/bar", "mode": "rw"}}
        return docker_client.containers.run(
            docker_client_built_image_name,
            [cmd],
            remove=True,
            volumes=volume,
            user=user,
        )

    cmd = "mkdir -p /bar && echo hello > /bar/hello.txt && chmod 700 /bar"
    _ = run_tesseract_with_volume(cmd)

    # Try to read the file as UID 1000
    read_cmd = "cat /bar/hello.txt"
    with pytest.raises(ContainerError) as e:
        _ = run_tesseract_with_volume(read_cmd, user="1000:1000")
    assert "Permission denied" in str(e)

    # Try to write to the folder as UID 1000
    write_cmd = "echo hello > /bar/hello_1000.txt && cat /bar/hello_1000.txt"
    with pytest.raises(ContainerError) as e:
        _ = run_tesseract_with_volume(write_cmd, user="1000:1000")
    assert "Permission denied" in str(e)

    # Grant permission to the file
    cmd = "chmod 777 /bar"
    _ = run_tesseract_with_volume(cmd)

    # Try to read the file as UID 1000 again
    stdout = run_tesseract_with_volume(read_cmd, user="1000:1000")
    assert stdout == b"hello\n"

    # Try to write to the folder as UID 1000 again
    stdout = run_tesseract_with_volume(write_cmd, user="1000:1000")
    assert stdout == b"hello\n"

    # Try to copy a file from a volume with permissions 700 to a volume with permission 777
    volume_777 = docker_client.volumes.create(name="docker_client_test_volume_777")
    docker_cleanup["volumes"].append(volume_777)
    volume_args = {
        docker_volume.name: {"bind": "/from", "mode": "rw"},
        volume_777.name: {"bind": "/to", "mode": "rw"},
    }
    cmd = "chmod 700 /from && cp /from/hello.txt /to/hello.txt && cat /to/hello.txt"
    stdout = run_tesseract_with_volume(cmd, volume=volume_args)
    assert stdout == b"hello\n"

    # Try to access files as UID1000
    cmd = "cat /to/hello.txt"
    stdout = run_tesseract_with_volume(cmd, user="1000:1000", volume=volume_args)
    assert stdout == b"hello\n"

    with pytest.raises(ContainerError) as e:
        run_tesseract_with_volume(
            "cat /from/hello_777.txt", user="1000:1000", volume=volume_args
        )
    assert "Permission denied" in str(e)

    cmd = (
        "adduser -D testuser && chmod 777 /from && su - testuser && cat /from/hello.txt"
    )
    stdout = run_tesseract_with_volume(cmd, volume=volume_args)
    assert stdout == b"hello\n"


def test_is_podman():
    """Test is_podman function.

    This assumes that the DOCKER_HOST environment variable is set to a Podman socket
    when running in a Podman environment. This is true on CI, but may deviate on
    local machines.
    """
    real_is_podman = "podman" in os.environ.get("DOCKER_HOST", "")
    assert is_podman() == real_is_podman


def test_is_valid_docker_tag():
    valid_tags = [
        "1.0.0",
        "v1.0.0",
        "sometag",
        "some-tag",
    ]
    for tag in valid_tags:
        assert _is_valid_docker_tag(tag)

    invalid_tags = [
        "0+unknown",
        "my/repo",
        "my\\tag",
        "a" * 129,
    ]
    for tag in invalid_tags:
        assert not _is_valid_docker_tag(tag)
