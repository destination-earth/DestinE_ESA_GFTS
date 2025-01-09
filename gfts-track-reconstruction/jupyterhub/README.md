# Deploying GFTS Hub

This is a log and record of deploying JupyterHub for GFTS

As much as possible, deployment uses automation via [OpenTofu][], [helm][], but there are always some manual steps.

[OpenTofu]: https://opentofu.org
[helm]: https://helm.sh

Initial manual steps:

1. create bucket for storing tofu state. Create user and store in `secrets/ovh-creds.sh`, and put bucket name in s3 backend configuration
2. create API token for OVH API, store in `secrets/ovh-creds.sh`

Next, run tofu within the `/deploy/tf` directory, which will create the kubernetes cluster

```bash
tofu init
tofu plan
tofu apply
```

At this point, we have a kubernetes cluster. Export the kubernetes cluster config:

```bash
export KUBECONFIG=$PWD/../jupyterhub/secrets/kubeconfig.yaml
tofu output -raw kubeconfig > $KUBECONFIG
chmod 600 $KUBECONFIG
kubectl config rename-context kubernetes-admin@gfts gfts
kubectl config use-context gfts
```

And login to the private image registry:

```bash
echo $(tofu output -raw registry_builder_token) | docker login $(tofu output -raw registry_url) --username $(tofu output -raw registry_builder_name) --password-stdin
```

Now we move to the `jupyterhub` directory.

Build the image with [chartpress](https://github.com/jupyterhub/chartpress):

```
chartpress --push
```

and deploy the chart with:

```
python deploy.py
```

Now jupyterhub should be running at https://gfts.minrk.net

## Background

`tofu` is used to deploy cloud resources.
Its configuration is in the `jupyterhub/tofu` directory.
We only need to use `tofu`
Once we have kubernetes running, we don't use `tofu` much anymore.
`tofu` is not run on CI, because its actions can be quite destructive.

`helm` is used to deploy things on kubernetes.
This is the main mechanism by which we modify our jupyterhub deployment.
This can be done on CI (but isn't yet).

There are two configuration files:

- gfts-hub/values.yaml is the main configuration file
- secrets/config.yaml is the file containing

`chartpress` is used to build our user image and update the helm chart

Deploying updates is two steps:

1. `chartpress` to ensure the image is up-to-date
2. `helm upgrade` to apply the changes

To deploy an update:

```
python3 deploy.py chartpress
python3 deploy.py helm
```

and cleanup your local files:

```
chartpress --reset
```

## The user image

The user image is defined in `images/user`.
To change what's in the image, modify `images/user/environment.yml` and run `make images/user/conda-linux-64.lock`.
