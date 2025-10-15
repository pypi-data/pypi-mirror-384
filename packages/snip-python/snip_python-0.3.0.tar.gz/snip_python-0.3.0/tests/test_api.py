import datetime
import io
from typing import Generic, TypeVar
import pytest
import requests
from abc import ABC, abstractmethod

import snip.api.schemas
from snip.api.snippets import get_snip_preview, upload_snip
from snip.token import BookToken
from snip.api.exceptions import AuthenticationException, BadRequestException
from snip.api.token import TokenMetadata, get_metadata
from snip.api.schemas import get_available_schemas, get_schema
import snip.api

T = TypeVar("T")
D = TypeVar("D")


class TestRequest(ABC, Generic[T, D]):
    url: str
    type = "GET"
    headers = {"content-type": "application/json"}

    @abstractmethod
    def call_api(self) -> T:
        pass

    @abstractmethod
    def response(self) -> D:
        """The expected result of the API call(s)."""

    @abstractmethod
    def assert_result(self, res: T):
        pass

    def mock_responses(self, requests_mock, **overwrites):
        kwargs = {
            "json": self.response(),
            "headers": self.headers,
            **overwrites,
        }
        if "exc" in overwrites:
            kwargs = {"exc": overwrites["exc"]}
        requests_mock.register_uri(self.type, self.url, **kwargs)

    def test_connection_timeout(self, requests_mock):
        self.mock_responses(requests_mock, exc=requests.exceptions.ConnectTimeout)
        with pytest.raises(requests.exceptions.ConnectTimeout):
            self.call_api()
        requests_mock.reset()

    def test_api_call(self, requests_mock):
        self.mock_responses(requests_mock)
        res = self.call_api()

        if isinstance(res, list):
            for r in res:
                self.assert_result(r)
        else:
            self.assert_result(res)

    def test_server_error(self, requests_mock):
        self.mock_responses(requests_mock, status_code=500)
        with pytest.raises(requests.exceptions.HTTPError):
            self.call_api()
        requests_mock.reset()

    def test_no_data(self, requests_mock):
        requests_mock.register_uri(self.type, self.url, json=None, status_code=200)
        with pytest.raises(ValueError):
            self.call_api()

    def test_bad_request(self, requests_mock):
        self.mock_responses(requests_mock, status_code=400)
        with pytest.raises(BadRequestException):
            self.call_api()
        requests_mock.reset()


@pytest.mark.skip(reason="This endpoint is currently broken")
class TestTokenMetadata(TestRequest):
    url = "https://test.de/api/token-meta"
    type = "POST"

    def call_api(self):
        return get_metadata(
            BookToken(
                name="test",
                book_id=123,
                token="asd",
                deployment_url="https://test.de",
            )
        )

    def response(self):
        return {
            "expires_at": "2021-01-01T00:00:00+00:00",
            "description": "test",
            "created_by": "test",
        }

    def assert_result(self, res: TokenMetadata):
        assert res["created_by"] == "test"
        assert res["description"] == "test"
        assert res["expires_at"] == datetime.datetime.fromisoformat(
            "2021-01-01T00:00:00+00:00"
        )

    def test_invalid_token(self, requests_mock):
        requests_mock.post(
            self.url,
            json={"message": "Invalid token provided."},
            status_code=401,
        )
        with pytest.raises(AuthenticationException):
            self.call_api()

        requests_mock.reset()
        requests_mock.post(
            self.url,
            json={"message": "Invalid token provided."},
            status_code=403,
        )
        with pytest.raises(AuthenticationException):
            self.call_api()

    def test_strange_data(self, requests_mock):
        requests_mock.post(
            self.url,
            json=["test"],
            status_code=200,
            headers=self.headers,
        )
        with pytest.raises(ValueError):
            self.call_api()


class TestAvailableSchemas(TestRequest):
    url = "https://test.de/schemas/json"

    def call_api(self):
        BookToken.deployment_url = "https://test.de"
        snip.api.DEFAULT_DEPLOYMENT_URL = "https://test.de"
        snip.api.schemas.DEFAULT_DEPLOYMENT_URL = "https://test.de"

        return [
            get_available_schemas("https://test.de"),
            get_available_schemas(),
        ]

    def response(self):
        return ["test"]

    def assert_result(self, res):
        assert res == ["test"]

    def test_strange_data(self, requests_mock):
        requests_mock.get(
            self.url,
            json={"test": "test"},
            status_code=200,
            headers={"content-type": "application/json"},
        )
        with pytest.raises(ValueError):
            self.call_api()


class TestSchema(TestRequest):
    url = "https://test.de/schemas/json/test"

    def call_api(self):
        BookToken.deployment_url = "https://test.de"
        snip.api.DEFAULT_DEPLOYMENT_URL = "https://test.de"

        return [
            get_schema("test", "https://test.de"),
            get_schema("test"),
        ]

    def response(self):
        return {"test": "test"}

    def assert_result(self, res):
        assert res == {"test": "test"}

    def test_strange_data(self, requests_mock):
        requests_mock.get(
            self.url,
            json=["test"],
            status_code=200,
            headers={"content-type": "application/json"},
        )
        with pytest.raises(ValueError):
            self.call_api()


from PIL import Image


class TestSnipPreview(TestRequest):
    url = "https://test.de/render/snip"
    type = "POST"
    headers = {"content-type": "image/png"}

    def call_api(self):
        t = BookToken(
            name="test",
            book_id=1,
            token="test",
            deployment_url="https://test.de",
        )
        text_snip = {"type": "text", "data": {"text": "Hallo"}}

        return get_snip_preview(text_snip, t)

    def response(self):
        # png image to binary
        byte_io = io.BytesIO()
        img = Image.new("RGB", (100, 100))
        img.save(byte_io, format="PNG")
        return byte_io.getvalue()

    def assert_result(self, res):
        assert isinstance(res, Image.Image)

    def mock_responses(self, requests_mock, **overwrites):
        kwargs = {
            "content": self.response(),
            "headers": {"content-type": "image/png"},
            **overwrites,
        }

        if "exc" in overwrites:
            kwargs = {"exc": overwrites["exc"]}

        requests_mock.register_uri(
            self.type,
            self.url,
            **kwargs,
        )

    def test_unidentifiedImageError(self, requests_mock):
        self.mock_responses(
            requests_mock, content=b"test", headers={"content-type": "image/png"}
        )
        with pytest.raises(Image.UnidentifiedImageError):
            self.call_api()

    def test_invalid_data(self, requests_mock):
        requests_mock.register_uri(
            self.type,
            self.url,
            json={"test": "test"},
            status_code=200,
            headers={"content-type": "application/json"},
        )
        with pytest.raises(ValueError):
            self.call_api()


class TestSnipUpload(TestRequest):
    url = "https://test.de/api/books/1/upload"
    type = "POST"
    headers = {"content-type": "application/json"}

    def call_api(self):
        t = BookToken(
            name="test",
            book_id=1,
            token="test",
            deployment_url="https://test.de",
        )
        text_snip = {"type": "text", "data": {"text": "Hallo"}}

        return upload_snip(text_snip, t)

    def response(self):
        return {"test": "test"}

    def assert_result(self, res):
        assert res == {"test": "test"}

    def test_exceptions(self):
        t = BookToken(
            name="test",
            book_id=2,
            token="test",
            deployment_url="https://test.de",
        )
        text_snip = {"type": "text", "data": {"text": "Hallo"}, "book_id": 1}
        with pytest.raises(ValueError):
            upload_snip(text_snip, t)

        # type not defined
        text_snip = {"data": {"text": "Hallo"}}
        with pytest.raises(ValueError):
            upload_snip(text_snip, t)

    def test_strange_data(self, requests_mock):
        requests_mock.post(
            self.url,
            json=["test"],
            status_code=200,
            headers={"content-type": "application/json"},
        )
        with pytest.raises(ValueError):
            self.call_api()
