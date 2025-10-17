# Snippets

Snippets are the building blocks of our lab book. They are small pieces of content that can shown on a page in the Snip Lab Book. Snippets can be of different types, such as text, images, or code.

This package among other things provides a number of implemented snippets that you may use to upload content and automate your workflow with the Snip Lab Book. You may also implement your own snippets or extend the implemented snippets.


## Implemented snippets

To find a list of all implemented snippets, please have a look at the [snippets](snip.snippets) module. 
For a more detailed description of the implemented snippets, please have a look at the following guides. We suggest you start with the image guide, as it is the most elaborate one and provides a good overview of how to use snippets in general.


```{toctree}
---
maxdepth: 1
---
snippets/image
snippets/text
snippets/combining
snippets/link
```


## Implementing own snippets

You may implement your own snips by extending the abstract snip [BaseClass](snip.snippets.base.BaseSnip). You may find more information in the Module documentation of the [snip.snippets](snip.snippets) module, depending on your needs you may also need to create the backend representation of this snippet for your deployment. Please see the general (non-python) snip documentation for more information on how to do this.
