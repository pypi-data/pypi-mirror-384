(cli/snippets)=
# Snippets

You can upload snippets to your lab books using the CLI. This is mainly a quality of life feature to make it easier to upload snippets without writing curl commands. This expects a valid token to be available, see [Token Management](#cli/token) for more information.

At the moment the `snippet` subcommand is barebones. We plan to add more features in the future if there is demand for it.

All commands related to tokens are available under the `snippet` subcommand.

```{typer} snip.app:snippet
---
theme: dimmed_monokai
width: 80
---
``` 

## Validate Snippets

To validate a snippet you may use the `snippet validate` command. This checks if a snippet is valid and can potentially be uploaded.

```{typer} snip.app:snippet:validate
---
theme: dimmed_monokai
width: 80
---
```

This check is only performed locally and does not require a token.


## Preview Snippets

To generate a preview of the snippet you may use `snippet preview`. This will open a window with the rendered snippet.

```{typer} snip.app:snippet:preview
---
theme: dimmed_monokai
width: 80
---
```

## Upload Snippets

To upload a snippet you may use the `snippet upload` command. This will upload the snippet to the lab book and it can be placed using the editor.

```{typer} snip.app:snippet:upload
---
theme: dimmed_monokai
width: 80
---
```