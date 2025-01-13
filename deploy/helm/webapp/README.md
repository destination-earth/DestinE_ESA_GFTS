# Helm chart for GFTS webapp

This helm chart handles the deployment of the GFTS webapp, it's ingress tied to a static IP and an oauth proxy in front of it.

Please make sure you have ssh-vault configured properly and you run the following commands in the helm chart directory before deploying the chart:

```bash
source ../../deploy/tf/secrets/ovh-creds.sh
envsubst < values-template.yaml > values.yaml
```
