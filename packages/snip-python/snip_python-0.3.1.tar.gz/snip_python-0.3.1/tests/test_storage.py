import pytest
from snip.token.storage import file_store, keyring_store, get_all_tokens
from snip.token import BookToken, AccountToken


class TestFileStore:
    def test_get_all_tokens(self, config_file):
        config_file, compare_tokens = config_file

        tokens, sources = file_store.get_all_tokens([config_file])

        assert len(tokens) == len(compare_tokens)
        assert len(sources) == len(compare_tokens)
        for i, token in enumerate(tokens):
            assert token.name == compare_tokens[i].name
            assert token.token == compare_tokens[i].token
            if isinstance(token, BookToken):
                assert token.book_id == compare_tokens[i].book_id
            assert isinstance(token.deployment_url, str)

    def test_get_all_tokens_invalid(self, invalid_config_file, caplog):
        config_file, compare_tokens = invalid_config_file

        tokens, sources = file_store.get_all_tokens([config_file])

        assert len(tokens) == len(compare_tokens)
        assert len(sources) == len(compare_tokens)

        # Check that we had a logging.warning
        assert len(caplog.records) != 0

    def test_duplicates(self, config_file, another_config_file, caplog):
        config_file, compare_tokens = config_file
        another_config_file, compare_tokens_another = another_config_file

        tokens, sources = file_store.get_all_tokens([config_file, another_config_file])

        assert len(tokens) == len(compare_tokens) + len(compare_tokens_another)
        assert len(sources) == len(compare_tokens) + len(compare_tokens_another)

        # Check that we had a logging.warning
        assert len(caplog.records) == 1
        assert "Duplicate token names!" in caplog.records[0].message

    def test_get_token(self, config_file):
        config_file, compare_tokens = config_file

        for token in compare_tokens:
            t = file_store.get_token(token.name, [config_file])
            assert t is not None
            assert t.name == token.name
            assert t.token == token.token
            if isinstance(t, BookToken):
                assert t.book_id == token.book_id
            assert isinstance(t.deployment_url, str)

        # Test not found
        t = file_store.get_token("nonexistent", [config_file])
        assert t is None

    def test_exists(self, config_file):
        config_file, compare_tokens = config_file

        for token in compare_tokens:
            assert file_store.token_exists(token.name, [config_file])

        assert not file_store.token_exists("nonexistent", [config_file])


class TestKeyringStore:
    def test_get_all_tokens(self, dummy_keyring, tokens):
        for token in tokens:
            keyring_store.save_token(token, dummy_keyring)

        tokens = keyring_store.get_all_tokens(dummy_keyring)
        assert len(tokens) == len(tokens)

    def test_invalid_kr_state(self, dummy_keyring, tokens, caplog):
        for token in tokens:
            keyring_store.save_token(token, dummy_keyring)

        dummy_keyring.delete_password(
            keyring_store.SNIP_KR_IDENTIFIER,
            tokens[0].name.encode("utf-8").hex() + ":book_id",
        )

        tokens_b = keyring_store.get_all_tokens(dummy_keyring)

        assert len(caplog.records) != 0
        assert len(tokens_b) == len(tokens) - 1

    def test_get_token(self, dummy_keyring, tokens):
        for token in tokens:
            keyring_store.save_token(token, dummy_keyring)

        for token in tokens:
            t = keyring_store.get_token(token.name, dummy_keyring)
            assert t is not None
            assert t.name == token.name
            assert t.token == token.token
            if isinstance(t, BookToken):
                assert t.book_id == token.book_id
            assert t.deployment_url == token.deployment_url

        # Test not found
        t = keyring_store.get_token("nonexistent", dummy_keyring)
        assert t is None

    def test_remove_token(self, dummy_keyring, tokens):
        for token in tokens:
            keyring_store.save_token(token, dummy_keyring)

        keyring_store.remove_token(tokens[0].name, dummy_keyring)

        tokens_b = keyring_store.get_all_tokens(dummy_keyring)

        assert len(tokens_b) == len(tokens) - 1

        # Remove non existing token
        with pytest.raises(ValueError):
            keyring_store.remove_token("nonexistent", dummy_keyring)

    def test_token_exists(self, dummy_keyring, tokens):
        for token in tokens:
            keyring_store.save_token(token, dummy_keyring)

        for token in tokens:
            assert keyring_store.token_exists(token.name, dummy_keyring)

        assert not keyring_store.token_exists("nonexistent", dummy_keyring)

    def test_save_with_overwrite(self, dummy_keyring, tokens):
        for token in tokens:
            keyring_store.save_token(token, dummy_keyring)

        for token in tokens:
            keyring_store.save_token(token, dummy_keyring, overwrite=True)

        # Expect error on duplicate
        for token in tokens:
            with pytest.raises(ValueError):
                keyring_store.save_token(token, dummy_keyring)


class TestGeneralStore:
    @pytest.fixture(autouse=True)
    def setup(self, dummy_keyring, config_file, tokens):
        for token in tokens:
            keyring_store.save_token(token, dummy_keyring)

        self.dummy_keyring = dummy_keyring
        self.config_file = config_file[0]
        self.tokens = list(tokens) + config_file[1]

        yield

    def test_get_all_tokens(self):
        tokens, sources = get_all_tokens(self.dummy_keyring, [self.config_file])
        assert len(tokens) == len(self.tokens)


class TestToken:
    def test_create_token(self):
        token = BookToken.from_unsafe("test", "asd", 123)

        assert token.name == "test"
        assert token.book_id == 123
        assert token.token == "asd"
        assert isinstance(token.deployment_url, str)

    def test_create_with_deployment_url(self):
        token = BookToken.from_unsafe("test", "asd", 123, BookToken.deployment_url)
        assert token.deployment_url == BookToken.deployment_url

    def test_from_unsafe_book(self, monkeypatch):
        BookToken.deployment_url = "https://test.de"
        monkeypatch.setattr(
            "snip.token.token.DEFAULT_DEPLOYMENT_URL", "https://test.de"
        )

        token = BookToken.from_unsafe(
            name="test",
            token="asd",
            book_id="123",
        )
        assert token.deployment_url == BookToken.deployment_url

        token = BookToken.from_unsafe(
            name="test",
            book_id="123",
            token="asd",
            deployment_url=None,
        )
        assert token.deployment_url == BookToken.deployment_url

        token = BookToken.from_unsafe(
            name="test",
            book_id="123",
            token="asd",
            deployment_url=BookToken.deployment_url,
        )
        assert token.deployment_url == BookToken.deployment_url
        assert token.type == "book"

    def test_from_unsafe_account(self):
        token = AccountToken.from_unsafe("test", "asd")
        assert token.name == "test"
        assert token.token == "asd"
        assert isinstance(token.deployment_url, str)
        assert token.type == "account"

    def test_repr(self):
        token = BookToken.from_unsafe("test", "asd", 123)
        r = repr(token)
        assert "BookToken" in r
        assert "test" in r
        assert "123" in r
        assert "https://" in r

        token = AccountToken.from_unsafe("test", "asd")
        r = repr(token)
        assert "AccountToken" in r
        assert "test" in r
        assert "https://" in r
