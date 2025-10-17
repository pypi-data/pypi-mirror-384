import pytest
from snip.token.token import BookToken
from typer.testing import CliRunner

from snip.__main__ import app


@pytest.fixture(scope="session")
def valid_snip_file(tmp_path_factory):
    file = tmp_path_factory.mktemp("data") / "valid_snip.json"
    file.write_text(
        """
{
    "type": "text",
    "data": {
        "text": "Hello, world!"
    },
    "book_id": 1
}
"""
    )
    return file


@pytest.fixture(scope="session", params=[1, 2, 3])
def invalid_snip_file(request, tmp_path_factory):
    file = tmp_path_factory.mktemp("data") / "invalid_snip.json"

    if request.param == 1:
        file.write_text(
            """
            {
                "type": "text",
                "data": {
                    "text": "Hello, world!"
                }
            }
            """
        )
    elif request.param == 2:
        file.write_text(
            """
            {
                "data": {
                    "text": "Hello, world!"
                },
                "book_id": "1"
            }
            """
        )
    elif request.param == 3:
        file.write_text(
            """
            {
                "type": "text",
                "data": {
                    "text1": "Hello, world!"
                },
                "book_id": "1"
            }
            """
        )
    return file


@pytest.fixture()
def mock_get_schema(monkeypatch):
    def get_schema(*args, **kwargs):
        return {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "data": {"type": "object"},
                "book_id": {"type": "integer"},
            },
            "required": ["type", "data", "book_id"],
        }

    monkeypatch.setattr("snip.snippets.__main__.get_schema", get_schema)


@pytest.fixture()
def mock_get_schema_invalid(monkeypatch):
    def get_schema(*args, **kwargs):
        raise ValueError("Invalid schema")

    monkeypatch.setattr("snip.snippets.__main__.get_schema", get_schema)


@pytest.fixture(params=[1, 2])
def mock_token_found(request, monkeypatch):
    def get_tokens_by_book_and_deployment(book_id, deployment):
        tokens = []
        sources = []
        for i in range(request.param):
            tokens.append(
                BookToken(
                    name=f"test{i}",
                    book_id=book_id,
                    token="asd",
                    deployment_url=deployment,
                )
            )
            sources.append("test")

        return tokens, sources

    monkeypatch.setattr(
        "snip.snippets.__main__.get_tokens_by_book_and_deployment",
        get_tokens_by_book_and_deployment,
    )


@pytest.fixture()
def mock_token_not_found(monkeypatch):
    def get_tokens_by_book_and_deployment(book_id, deployment):
        return [], []

    monkeypatch.setattr(
        "snip.snippets.__main__.get_tokens_by_book_and_deployment",
        get_tokens_by_book_and_deployment,
    )


from PIL import Image


@pytest.fixture(autouse=True)
def mock_preview(monkeypatch):
    def preview(*args, **kwargs) -> Image.Image:
        img = Image.new("RGB", (100, 100))

        return img

    monkeypatch.setattr("snip.snippets.__main__.get_snip_preview", preview)


@pytest.fixture(autouse=True)
def mock_os_system(monkeypatch):
    def os_system(*args, **kwargs):
        return 0

    monkeypatch.setattr("os.system", os_system)


class TestSnipCli:
    runner = CliRunner()

    def test_validate(
        self, valid_snip_file, mock_get_schema, caplog: pytest.LogCaptureFixture
    ):
        caplog.set_level("WARNING")
        result = self.runner.invoke(
            app,
            [
                "snippet",
                "validate",
                str(valid_snip_file),
            ],
        )
        assert result.exit_code == 0

        # Caplog does not include warnings or errors
        assert len(caplog.records) == 0

    def test_invalid_validate(
        self, invalid_snip_file, mock_get_schema, caplog: pytest.LogCaptureFixture
    ):
        caplog.set_level("WARNING")
        result = self.runner.invoke(
            app,
            [
                "snippet",
                "validate",
                str(invalid_snip_file),
            ],
        )
        assert result.exit_code != 0

    def test_invalid_schema(
        self, valid_snip_file, mock_get_schema_invalid, caplog: pytest.LogCaptureFixture
    ):
        caplog.set_level("WARNING")
        result = self.runner.invoke(
            app,
            [
                "snippet",
                "validate",
                str(valid_snip_file),
            ],
        )
        assert result.exit_code != 0

    def test_preview(self, valid_snip_file, mock_get_schema, mock_token_found):
        result = self.runner.invoke(
            app,
            [
                "snippet",
                "preview",
                str(valid_snip_file),
            ],
        )
        assert result.exit_code == 0

        # Test with manual token
        result = self.runner.invoke(
            app,
            [
                "snippet",
                "preview",
                str(valid_snip_file),
                "--token",
                "asd",
            ],
        )

    def test_preview_no_token(
        self, valid_snip_file, mock_get_schema, mock_token_not_found
    ):
        result = self.runner.invoke(
            app,
            [
                "snippet",
                "preview",
                str(valid_snip_file),
            ],
        )
        assert result.exit_code != 0
