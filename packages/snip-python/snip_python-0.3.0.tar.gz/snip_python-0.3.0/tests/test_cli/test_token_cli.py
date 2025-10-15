from typer.testing import CliRunner

from snip.__main__ import app
from snip.token.storage import keyring_store


class TestTokenCli:
    runner = CliRunner()

    def test_rm_token(self, monkeypatch, dummy_keyring, tokens):
        monkeypatch.setattr("snip.token.__main__.get_keyring", lambda: dummy_keyring)
        for token in tokens:
            keyring_store.save_token(token, dummy_keyring)

        assert len(keyring_store.get_all_tokens(dummy_keyring)) == len(tokens)

        result = self.runner.invoke(app, ["token", "remove", tokens[0].name])

        assert result.exit_code == 0

        b_tokens = keyring_store.get_all_tokens(dummy_keyring)
        assert len(b_tokens) == len(tokens) - 1

    def test_rm_token_nonexistent(self, monkeypatch, dummy_keyring, tokens):
        monkeypatch.setattr("snip.token.__main__.get_keyring", lambda: dummy_keyring)
        for token in tokens:
            keyring_store.save_token(token, dummy_keyring)

        assert len(keyring_store.get_all_tokens(dummy_keyring)) == len(tokens)

        result = self.runner.invoke(app, ["token", "remove", "nonexistent"])
        assert result.exit_code == 2
        assert "not found" in result.output

    def test_list_tokens(self, monkeypatch, dummy_keyring, caplog, tokens):
        monkeypatch.setattr("snip.token.__main__.get_keyring", lambda: dummy_keyring)
        result = self.runner.invoke(app, ["token", "list"])
        assert result.exit_code == 0
        assert "No tokens found!" in result.output

        # Set some tokens
        for token in tokens:
            keyring_store.save_token(token, dummy_keyring)

        result = self.runner.invoke(app, ["token", "list"])
        assert result.exit_code == 0

        for token in tokens:
            assert token.name in result.output

    def test_list_no_keyring(self, monkeypatch, dummy_keyring, tokens):
        monkeypatch.setattr("snip.token.__main__.get_keyring", lambda: None)
        result = self.runner.invoke(app, ["token", "list"])

        assert "No keyring selected." in result.output

    def test_add_token(self, monkeypatch, dummy_keyring):
        monkeypatch.setattr("snip.token.__main__.get_keyring", lambda: dummy_keyring)

        result = self.runner.invoke(
            app,
            [
                "token",
                "add",
                "TEST",
                "--name",
                "foo",
                "--book-id",
                "1",
            ],
        )
        print(result.output)
        assert result.exit_code == 0

        token = keyring_store.get_token("foo", dummy_keyring)
        assert token is not None
