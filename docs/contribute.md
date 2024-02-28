# How to contribute

To contribute to this repository, bplease refer to our
[Rule of Participation](rule_of_participation) as well as our
[Code of Conduct](code_of_conduct) documents.

## Writing docs

Our docs are written using JupyterBook. To contribute to the docs,
install the python dependencies

```bash
pip install jupyter-book sphinx-exercise sphinx-autobuild
```

And then run a small sphinx server with live-reload functionality

```bash
cd docs
sphinx-autobuild . _build/html -b html
```
