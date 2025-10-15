# Snip

![PyPI - Version](https://img.shields.io/pypi/v/snip-python?logoColor=green&color=%234bc51d)
[![Documentation Status](https://readthedocs.org/projects/snip-python/badge/?version=latest)](https://snip-python.readthedocs.io/en/latest/?badge=latest)

Python Package of quality of life and helper functions to interface with the Snip Lab Book. Allows to create and upload snippets with relative ease. Store and retrieve api tokens, and more.

## Features

<!-- start features -->

- **Token management**: Store and retrieve api tokens in a secure keyring or in a configuration files.
- **Python API**: Python API to create and upload snippets to your lab books.
- **CLI**: Command line interface to interact with the Snip API.
- **API Wrappers**: Wrappers for the Snip API to make requests and handle responses.

<!-- end features -->

## Quickstart

<!-- start quickstart -->

Snip is distributed on [PyPI]. To use the package:

1. Install the package using pip:

```bash
pip install snip-python
```
2. Use the `snip` command line interface (CLI) to interact with your lab books. For example, you can use the `snip token` command to store and retrieve your API tokens.

```bash
snip token --help
```

3. Create and upload snippets to your lab books programmatically using the Python API.

```python
from snip.snippets import ImageSnip

snip = ImageSnip.from_path("path/to/image.png", book_id="[YOUR_BOOK_ID]")

# show a preview of the snippet
snip.preview()
```

If you need help figuring out where to find the book id, please have a look [here](https://snip-python.readthedocs.io/en/latest/tokens.html#how-to-find-the-book-id).

```python
# upload the snippet
snip.upload()
```

The upload will automatically search your tokens in the keyring or in the configuration file and use the correct token to upload the snippet.

[pypi]: https://pypi.org/project/snip-python/

<!-- end quickstart -->


For more information, visit [documentation][quickstart-docs].

[quickstart-docs]: https://snip-python.readthedocs.io/en/latest/quickstart.html

