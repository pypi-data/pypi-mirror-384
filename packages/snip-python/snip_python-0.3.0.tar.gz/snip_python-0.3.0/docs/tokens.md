# Access Tokens

Additionally to the [cli tool](cli) to manage your tokens, you may also use the python API or 
use configuration files to manage your tokens.

Please see the [token.storage](snip.token.storage) module for more information on how to store and retrieve tokens via the python API.


## File Structure

We automatically load tokens from the following locations:

- `~/.sniprc` (Your home directory)
- `./.sniprc` (Current working directory)
- `/etc/snip/.sniprc` (System wide configuration)
- `SNIPRC` environment variable (Path to a configuration file)

The files should follow ini file format and have the following structure:

```ini
[unique_token_name]
book_id = 1
token = your_token
deployment_url = https://snip.roentgen.physik.uni-goettingen.de
type = book | account
```

The deployment URL is optional and will default to `https://snip.roentgen.physik.uni-goettingen.de` if not provided.

## How to create a token?

You can find an entry to create tokens in the [books settings](https://snip.roentgen.physik.uni-goettingen.de) of each of your Lab Books. The URL may vary depending on your deployment. If you want to create an account token, you may find the entry in your [account settings](https://snip.roentgen.physik.uni-goettingen.de/account/misc).

## How to find the book_id?

The book_id is the unique identifier of your lab book in your deployment. The easiest way to find it is to look at the URL of the lab book editor in a browser.
For example, if your open the editor of your book at `https://snip.roentgen.physik.uni-goettingen.de/book/1542`, the book_id is `1542`.