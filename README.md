# Global Fish Tracking Service (GFTS)

A Destination Earth Platform use case.

[![GFTS Jupyter book](https://github.com/destination-earth/DestinE_ESA_GFTS/actions/workflows/deploy.yml/badge.svg)](https://github.com/destination-earth/DestinE_ESA_GFTS/blob/main/.github/workflows/deploy.yml)

[![GFTS Jupyter Hub](https://github.com/destination-earth/DestinE_ESA_GFTS/actions/workflows/deploy-hub.yaml/badge.svg)](https://github.com/destination-earth/DestinE_ESA_GFTS/blob/main/.github/workflows/deploy-hub.yaml)

## The GFTS in a nutshell

The lack of accurate modelling of fish movement, migration strategies, and site fidelity is a major challenge for policy-makers when they need to formulate effective conservation policies.
By relying on the Pangeo infrastructure on the DestinatE Platform, the Use Case aims to predict the sea bass behavior and develop a Decision Support Tool (DST) for “what-if” scenario planning.
As a result, the Use Case will help to obtain accurate insights into fish populations by introducing the Global Fish Tracking System (GFTS) and a Decision Support Tool into the DestinE Platform.

## Authors

### Active contributors

- [@minrk](https://www.github.com/minrk)
- [@annefou](https://www.github.com/annefou)
- [@yellowcap](https://www.github.com/yellowcap)
- [@tinaok](https://www.github.com/tinaok)
- [@aderrien7](https://www.github.com/aderrien7)

## Contributing

Contributions are always welcome!

Tho contribute to DestinE Open Source SW collections please refer to [Rule of Participation](docs/rule_of_participation.md)

## Code of Conduct

DestinE open source community abide to this [Code of Conduct](docs/code_of_conduct.md)## Deployment of GFTS Hub on the cloud

Instructions on how to build and deploy GFTS hub are described in [./gfts-track-reconstruction/jupyterhub/README.md](https://github.com/destination-earth/DestinE_ESA_GFTS/blob/main/gfts-track-reconstruction/jupyterhub/README.md).

The current Jupyterhub deployment is done on OVH cloud operator.

## Documentation

Documentation can be viewed at [https://destination-earth.github.io/DestinE_ESA_GFTS](https://destination-earth.github.io/DestinE_ESA_GFTS).

<a href="https://w3id.org/ro-id/2edcfa66-0f59-42f4-aa29-1c5681466424"> <img alt="RoHub" src="https://img.shields.io/badge/RoHub-FAIR_Executable_Research_Object-2ea44f?logo=Open+Access&logoColor=blue"></a>

## Feedback

If you have any feedback, please reach out to us by filling an [issue](https://github.com/destination-earth/DestinE_ESA_GFTS/issues/new).

## Run Locally

### Clone the github repository

To get a local copy of the GFTS repository, you can clone it on your local computer and/or server:

```bash
git clone https://github.com/destination-earth/DestinE_ESA_GFTS.git
```

### Install and run DestinE_ESA_GFTS jupyter notebooks locally from source

Jupyter notebooks to showcase GFTS are in the `docs` folder and can be run after installing Python and the required packages listed in the [.binder/environment.yml](https://raw.githubusercontent.com/annefou/DestinE_ESA_GFTS/main/.binder/environment.yml) file.

#### Install Python

To install Python, we recommend to install [conda](https://conda.io/projects/conda/en/latest/index.html) or [miniconda](https://docs.anaconda.com/free/miniconda/) and then create a new conda environment using [.binder/environment.yml](https://raw.githubusercontent.com/annefou/DestinE_ESA_GFTS/main/.binder/environment.yml):

```bash
conda env create -f environment.yml
```

Do not forget to switch to the `gfts` conda environment prior to executing any Jupyter notebooks or programs from the GFTS repository.

```bash
conda activate gfts
```

To deactivate the `gfts` environment:

```bash
conda deactivate
```

#### Start JupyerLab and run the Jupyter notebooks

Once all the required packages are installed, you can start JupyterLab and run the jupyter notebooks from the `docs` folder:

```bash
jupyter lab
```

### Install and run DestinE_ESA_GFTS with containers

Before building the GFTS docker image, you would need to install [docker](https://docs.docker.com/engine/install/).

### Build docker container

Make sure you change directory to `gfts-track-reconstruction/jupyterhub/images/user` before executing the command below:

```bash
docker build -t gfts:latest .
```

#### Run GFTS from docker

```bash
docker run -p 7777:8888 -i -t gfts:latest jupyter lab --ip=0.0.0.0 --no-browser
```

Open your web browser and enter the following command:

```bash
http://127.0.0.1:7777/lab
```

Then you need to enter your token: it can be found at the bottom of the printout you got after running the docker run command given above.

## Support

For support, please create a Github [issue](https://github.com/destination-earth/DestinE_ESA_GFTS/issues/new).

## Used By

This project is used by the following companies:

- [IFREMER](https://www.ifremer.fr)
- [Development Seed](http://developmentseed.org)
- [Simula](http://simula.no)

## 🛠 Skills

Python, Jupyter Notebooks.

## License

All documentation and chapter materials in this repository are made available under the CC-BY-4 and the software are made available under the Apache-2 licence; for more details, see the [LICENSE file](https://github.com/destination-earth/DestinE_ESA_GFTS/blob/main/LICENSE).
