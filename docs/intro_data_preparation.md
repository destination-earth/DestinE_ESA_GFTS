# Introduction

This subsection aims to introduce you to the two types of data used in this project:
1. _Reference models_, which refers to the data catalogues of the [Copernicus Service's services](https://www.copernicus.eu/en/copernicus-services) such as [CMEMS](https://marine.copernicus.eu/), the one we are the most interested by in `GFTS`.
2. _Tag data_, that corresponds to any information and measurements collected from a tagged fish, ranging from the name of the tagging campaign to the temperature/pressure time series.

Here a brief overview of what each section guides you through:

* **_Create Kerchunk catalog for CMEMS_** and its 3D version show how to build a reference model.
* **_Read parquet kerchunk catalog_** illustrates how to load an already built reference model saved on the S3 bucket.
* **_Create a Reference Model with `virtualizarr`_** presents another way for building reference models, this time with a recent library called `virtualizarr`.
* one the other hand, **_Tag Data Preparation_** describes one way of processing raw tag data.
* **_Copernicus data exploration_** and **_Reading CMEMS Copernicus data from GFTS s3 bucket_** illustrate how to wrap several reference models into a single [YAML intake catalogue](https://intake.readthedocs.io/en/latest/catalog.html#yaml-format).

While the rest of the chapters focus on visualization of the different data.