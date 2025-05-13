# GFTS Workflow

The GFTS project aims to provide users tools for analyzing data from tagged fish and estimating the fish locations.
This is done through what we refer to as the _GFTS workflow_.
As mentioned in the previous section, this project will use [`pangeo-fish`](https://github.com/pangeo-fish/pangeo-fish) for estimating the fish locations.

## Steps

The GFTS Workflow can be described as a vertical pipeline, whose main steps are the following:

1. **Data Preparation:** preparation of the input data for `pangeo-fish`.
2. **Execution:** run of the geolocation model implemented by `pangeo-fish` on all the biologging data.
3. **Scientific Validation:** in-depth analysis of the results and data validation (assumed to be partly done with `pangeo-fish`).
4. **Result Publication:** preparation and submission of the results to the GFTS Service.

In the next chapter, we go through these steps in more details.

## File Management

Throughout the workflow, data is saved and/or loaded remotely (to the so-called "bucket").
Therefore, it is important to keep a consistent file structure across the users and data types.
Notably, the high-level hierarchy within a result directory is the tag, through its unique identifier `id`, e.g.:

```
your_tag_folder
├── id_0
│   ├── common_file1.html
│   ├── common_file2.csv
│   ├── ...
│   ├── configuration_0/trajectory.html
│   ├── configuration_0/video.mp4
│   ├── configuration_1/states.zarr
│   └── configuration_1/trajectory.html
├── id_1
│   └── ...
└── ...
```

This organization is easy to automatically implement and follow with `pangeo_fish`'s I/O operations.
With some practice, you will quickly be familiar with this file structure!
