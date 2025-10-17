(cli/index)=
# Command Line Interface (CLI)

We provide a command line interface (CLI) which should be available after installing the package. You can access the help message by running:

```{typer} snip.app
---
prog: snip
theme: dimmed_monokai
width: 80
---
``` 

:::{admonition} Troubleshooting
:class: warning

If the `snip` command is not available, make sure that the package is installed in the correct environment. Alternatively, you can run the command using the Python interpreter:

```bash
python -m snip --help
```
:::

## Features

The CLI provides the following features:

```{toctree}
---
maxdepth: 1
hidden: true
---

cli/token
cli/snippets
```


- **[Tokens](<project:./cli/token.md>)**: Store, remove and retrieve API tokens in a secure keyring or in a configuration file.
- **[Snippets](<project:./cli/snippets.md>)**: Validate snippets or upload them to your lab books using the CLI.




