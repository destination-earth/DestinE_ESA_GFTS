images/user/conda-linux-64.lock: images/user/environment.yml images/user/virtual-packages.yaml
	conda-lock lock -k explicit --mamba --channel conda-forge --platform linux-64 --virtual-package-spec images/user/virtual-packages.yaml --filename-template $@ -f $<

cert-manager:
	helm repo add jetstack https://charts.jetstack.io --force-update
	helm install --upgrade --namespace cert-manager jetstack/cert-manager --create-namespace --version v1.13.3 --set installCRDs=true
