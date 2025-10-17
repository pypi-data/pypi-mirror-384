
(cli/token)=
# Token Management

You may add, remove and interact with tokens using the CLI. By default tokens are stored in a secure keyring. We recommend using the keyring to store your tokens but you can also store them in a configuration file.

All commands related to tokens are available under the `token` subcommand.

```{typer} snip.app:token
---
theme: dimmed_monokai
width: 80
---
``` 


## Adding and Removing Tokens

You may add tokens to the keyring using the `token add` command:

```{typer} snip.app:token:add
---
theme: dimmed_monokai
width: 80
---
```

You may also remove tokens from the keyring using the `token remove` command:

```{typer} snip.app:token:remove
---
theme: dimmed_monokai
width: 80
---
```

## Listing available Tokens

To get an overview of available tokens, you may list all tokens available in the keyring and through the configuration files using the `token list` command:

```{typer} snip.app:token:list
---
theme: dimmed_monokai
width: 80
---
```

:::{admonition} Troubleshooting
:class: warning

Token keyring management depends on the `keyring` package. 

It is possible that a `token add` command does not work as expected and tokens do not appear in the list if the `NULL` keyring backend is selected. This can be fixed by setting the keyring backend via the `-k` or using the env variable `PYTHON_KEYRING_BACKEND`. 

Either set the environment variable:

```bash
export PYTHON_KEYRING_BACKEND=keyring.backends.chainer.ChainerBackend
```

or using the `-k` flag:

```bash
snip token add -k keyring.backends.chainer.ChainerBackend
```
:::