# GFTS webapp

The webapp for this project is being developed in its own repository: [github.com/developmentseed/gfts](https://github.com/developmentseed/gfts).

Here, we will document how to deploy the webapp.

## Container

The webapp can be run in a container. The Dockerfile is in the `webapp` directory of the repository.

## Deployment

### Infrastructure

As a requirement for the webapp, we need a kubernetes cluster, which needs to be setup manually as OVH Cloud doesn't support terraform for their high availability zone.
Then everything is managed through helm charts in `deploy/webapp/helm`
