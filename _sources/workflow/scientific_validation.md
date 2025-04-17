# 3. Scientific Validation of the results

This guide covers the third step of the workflow, where the user aims to analyze the results computed in the [previous step](geolocation_model_execution.md) (i.e. fish locations estimations).

_As such, this section is intended to more **advanced users**, who are responsible for closely analyzing the data and eventually validating it._

<!-- In this tutorial, we illustrate a way to explore the results, but rendered in two different ways: either as a [panel](https://panel.holoviz.org/index.html) webpage, and directly in the JupyterLab. -->

In this tutorial, we explore the results by serving a [panel](https://panel.holoviz.org/index.html) webpage.
To that aim, we will first illustrate another use of `kbatch-papermill` by implementing a notebook that will render and save a plot for each tag processed in the previous [tutorial](papermill_launcher2.ipynb).
