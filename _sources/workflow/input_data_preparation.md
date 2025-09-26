# 1. Data Preparation for `pangeo_fish`

In a nutshell, as you might already know, estimating the fish locations consists of comparing sensor data from tagged fish with oceanic data, known as _reference_ or _field_ models.

Throughout this documentation, we will refer to the information collected from tags as _biologging data_ (or just _tags_), while the oceanic models will be referred to as _reference models_.
Depending on the tagging campaign, the reference data can include temperature, bathymetry or light data.

In this section, we detail:

1. How to pre-process the raw data from tags to plug in to `pangeo_fish`.
2. How to assemble a reference with `virtualizarr`.
