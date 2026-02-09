import glob
import os
import tempfile
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from rdflib_endpoint.__main__ import cli

runner = CliRunner()

out_formats = ["ttl", "nt", "xml", "jsonld", "trig"]


def test_convert() -> None:
    for out_format in out_formats:
        with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
            out_file = f"{tmp_file.name}.{out_format}"
            result = runner.invoke(
                cli,
                ["convert", "tests/resources/test2.ttl", "--output", out_file],
            )
            assert result.exit_code == 0
            with open(out_file) as file:
                content = file.read()
                assert len(content) > 1

    # Fix issue with python creating unnecessary temp files on disk
    for f in glob.glob("<tempfile._TemporaryFileWrapper*"):
        os.remove(f)


def test_convert_oxigraph() -> None:
    with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
        result = runner.invoke(
            cli,
            [
                "convert",
                "--store",
                "oxigraph",
                "tests/resources/test2.ttl",
                "--output",
                tmp_file.name,
            ],
        )
        assert result.exit_code == 0
        with open(tmp_file.name) as file:
            content = file.read()
            assert len(content) > 1
    # Fix issue with python creating unnecessary temp files on disk
    for f in glob.glob("<tempfile._TemporaryFileWrapper*"):
        os.remove(f)


# NOTE: Needs to run last tests, for some reason patching uvicorn as a side effects on follow up tests


@patch("rdflib_endpoint.__main__.uvicorn.run")
def test_serve(mock_run: MagicMock) -> None:
    """Test serve, mock uvicorn.run to prevent API hanging"""
    mock_run.return_value = None
    result = runner.invoke(
        cli,
        [
            "serve",
            "tests/resources/test.nq",
            "tests/resources/test2.ttl",
            "tests/resources/another.jsonld",
        ],
    )
    assert result.exit_code == 0


@patch("rdflib_endpoint.__main__.uvicorn.run")
def test_serve_oxigraph(mock_run: MagicMock) -> None:
    """Test serve oxigraph, mock uvicorn.run to prevent API hanging"""
    mock_run.return_value = None
    result = runner.invoke(
        cli,
        [
            "serve",
            "--store",
            "oxigraph",
            "tests/resources/test.nq",
            "tests/resources/test2.ttl",
            "tests/resources/another.jsonld",
        ],
    )
    assert result.exit_code == 0
