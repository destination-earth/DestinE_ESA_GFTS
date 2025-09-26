# 2. Estimation of fish locations

The second step of the GFTS workflow aims to process each tag of a tagging campaign with `pangeo_fish`.
In this project, the executions are launched with the help of `kbatch_papermill` (introduced in the next page).
In short, the core idea is to let you write notebooks, whose computations will be centered on a tag, and launch them automatically with the package mentioned above with all the tags.
