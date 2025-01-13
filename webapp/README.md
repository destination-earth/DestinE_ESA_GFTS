# GFTS webapp

The webapp for this project is being developed in its own repository: [github.com/developmentseed/gfts](https://github.com/developmentseed/gfts).

Here, we will document how to deploy the webapp.

## Container

The webapp can be run in a container. The Dockerfile is in the `webapp` directory of the repository.

## Deployment

### Infrastructure

As a requirement for the webapp, we need a kubernetes cluster. Then the webapp consists in two parts to:

- terraform/tofu resources for a static floating IP address in `deploy/tf`
- helm charts for a configured kubernetes cluster `deploy/helm/webapp`
