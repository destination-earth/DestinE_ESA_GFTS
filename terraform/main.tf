terraform {
  required_version = "~> 1.6"
  required_providers {
    ovh = {
      source  = "ovh/ovh"
      version = "~> 0.36.1"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    harbor = {
      source  = "BESTSELLER/harbor"
      version = "~> 3.7"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }
  # store state on gcs, like other clusters
  backend "s3" {
    bucket                      = "tf-state-gfts"
    key                         = "terraform.tfstate"
    region                      = "gra"
    endpoint                    = "s3.gra.io.cloud.ovh.net"
    skip_credentials_validation = true
    skip_region_validation      = true
  }
}

provider "ovh" {
  endpoint = "ovh-eu"
  # credentials loaded via source ./secrets/ovh-creds.sh
}

locals {
  service_name = "2a0ebfcd5a8d46a797b921841717b052"
  cluster_name = "gfts"
  # GRA9 is colocated with registry
  region = "GRA11"
}

# create a private network for our cluster
resource "ovh_cloud_project_network_private" "network" {
  service_name = local.service_name
  name         = "gfts" # local.cluster_name
  regions      = [local.region]
}

resource "ovh_cloud_project_network_private_subnet" "subnet" {
  service_name = local.service_name
  network_id   = ovh_cloud_project_network_private.network.id

  region  = local.region
  start   = "10.0.0.100"
  end     = "10.0.0.254"
  network = "10.0.0.0/24"
  dhcp    = true
}

import {
  to = ovh_cloud_project_kube.cluster
  id = "2a0ebfcd5a8d46a797b921841717b052/899fbf3a-988c-4054-8945-c6fb5fef858c"
}

resource "ovh_cloud_project_kube" "cluster" {
  service_name = local.service_name
  name         = local.cluster_name
  region       = local.region
  # version      = "1.28"
  # make sure we wait for the subnet to exist
  depends_on = [ovh_cloud_project_network_private_subnet.subnet]

  # private_network_id is an openstackid for some reason?
  private_network_id = tolist(ovh_cloud_project_network_private.network.regions_attributes)[0].openstackid

  # customization_apiserver {
  #   admissionplugins {
  #     enabled = ["NodeRestriction"]
  #     # disable AlwaysPullImages, which causes problems
  #     disabled = ["AlwaysPullImages"]
  #   }
  # }
  update_policy = "MINIMAL_DOWNTIME"
}

# ovh node flavors: https://www.ovhcloud.com/en/public-cloud/prices/

resource "ovh_cloud_project_kube_nodepool" "core" {
  service_name = local.service_name
  kube_id      = ovh_cloud_project_kube.cluster.id
  name         = "core-202401"
  # b2-15 is 4 core, 15GB
  flavor_name = "b3-8"
  max_nodes   = 2
  min_nodes   = 1
  autoscale   = true
  template {
    metadata {
      annotations = {}
      finalizers  = ["ovhcloud.com/v1beta1", "ovhcloud.com/v1"]
      labels = {
        "hub.jupyter.org/node-purpose" = "core"
      }
    }
    spec {
      unschedulable = false
      taints        = []
    }
  }
  lifecycle {
    ignore_changes = [
      # don't interfere with autoscaling
      desired_nodes
    ]
  }
}

resource "ovh_cloud_project_kube_nodepool" "user" {
  service_name = local.service_name
  kube_id      = ovh_cloud_project_kube.cluster.id
  name         = "user-202401"
  # r2-120 is 8 core, 120GB
  flavor_name = "b3-16"
  max_nodes   = 1
  min_nodes   = 0
  autoscale   = true
  template {
    metadata {
      annotations = {}
      finalizers  = ["ovhcloud.com/v1beta1", "ovhcloud.com/v1"]
      labels = {
        "hub.jupyter.org/node-purpose" = "users"
      }
    }
    spec {
      unschedulable = false
      taints        = []
    }
  }
  lifecycle {
    ignore_changes = [
      # don't interfere with autoscaling
      desired_nodes
    ]
  }
}


output "kubeconfig" {
  value       = ovh_cloud_project_kube.cluster.kubeconfig
  sensitive   = true
  description = <<EOF
    # save output with:
    export KUBECONFIG=$PWD/../jupyterhub/secrets/kubeconfig.yaml
    tofu output -raw kubeconfig > $KUBECONFIG
    chmod 600 $KUBECONFIG
    kubectl config rename-context kubernetes-admin@gfts gfts
    kubectl config use-context gfts
    EOF
}

# deploy cert-manager

provider "kubernetes" {
  host                   = ovh_cloud_project_kube.cluster.kubeconfig_attributes[0].host
  client_certificate     = base64decode(ovh_cloud_project_kube.cluster.kubeconfig_attributes[0].client_certificate)
  client_key             = base64decode(ovh_cloud_project_kube.cluster.kubeconfig_attributes[0].client_key)
  cluster_ca_certificate = base64decode(ovh_cloud_project_kube.cluster.kubeconfig_attributes[0].cluster_ca_certificate)
}

resource "kubernetes_namespace" "cert-manager" {
  metadata {
    name = "cert-manager"
  }
}

provider "helm" {
  kubernetes {
    host                   = ovh_cloud_project_kube.cluster.kubeconfig_attributes[0].host
    client_certificate     = base64decode(ovh_cloud_project_kube.cluster.kubeconfig_attributes[0].client_certificate)
    client_key             = base64decode(ovh_cloud_project_kube.cluster.kubeconfig_attributes[0].client_key)
    cluster_ca_certificate = base64decode(ovh_cloud_project_kube.cluster.kubeconfig_attributes[0].cluster_ca_certificate)
  }
}

resource "helm_release" "cert-manager" {
  name       = "cert-manager"
  namespace  = kubernetes_namespace.cert-manager.metadata[0].name
  repository = "https://charts.jetstack.io"
  chart      = "cert-manager"
  version    = "1.13.3"

  set {
    name  = "installCRDs"
    value = true
  }
  # match ClusterIssuer in gfts-hub chart
  set {
    name  = "ingressShim.defaultIssuerKind"
    value = "ClusterIssuer"
  }
  set {
    name  = "ingressShim.defaultIssuerName"
    value = "letsencrypt-prod"
  }
}

# registry

data "ovh_cloud_project_capabilities_containerregistry_filter" "registry_plan" {
  service_name = local.service_name
  # SMALL is 200GB
  # MEDIUM is 600GB
  # LARGE is 5TiB
  plan_name = "SMALL"
  region    = "GRA"
}

resource "ovh_cloud_project_containerregistry" "registry" {
  service_name = local.service_name
  plan_id      = data.ovh_cloud_project_capabilities_containerregistry_filter.registry_plan.id
  region       = data.ovh_cloud_project_capabilities_containerregistry_filter.registry_plan.region
  name         = "gfts"
}

# admin user (needed for harbor provider)
resource "ovh_cloud_project_containerregistry_user" "admin" {
  service_name = ovh_cloud_project_containerregistry.registry.service_name
  registry_id  = ovh_cloud_project_containerregistry.registry.id
  email        = "gfts-registry-admin@ovh.local"
  login        = "gfts-registry-admin"
}


# now configure the registry via harbor itself
provider "harbor" {
  url      = ovh_cloud_project_containerregistry.registry.url
  username = ovh_cloud_project_containerregistry_user.admin.login
  password = ovh_cloud_project_containerregistry_user.admin.password
}

resource "harbor_project" "registry" {
  name = "gfts"
}

resource "harbor_robot_account" "builder" {
  name        = "builder"
  description = "Image builder: push new images"
  level       = "project"
  permissions {
    access {
      action   = "push"
      resource = "repository"
    }
    access {
      action   = "pull"
      resource = "repository"
    }
    kind      = "project"
    namespace = harbor_project.registry.name
  }
}

resource "harbor_robot_account" "puller" {
  name        = "puller"
  description = "Pull access to images"
  level       = "project"
  permissions {
    access {
      action   = "pull"
      resource = "repository"
    }
    kind      = "project"
    namespace = harbor_project.registry.name
  }
}


# resource "harbor_retention_policy" "builds" {
#   # run retention policy on Saturday morning
#   scope    = harbor_project.registry.id
#   schedule = "0 0 7 * * 6"
#   # rule {
#   #   repo_matching        = "**"
#   #   tag_matching         = "**"
#   #   most_recently_pulled = 1
#   #   untagged_artifacts   = false
#   # }
#   rule {
#     repo_matching          = "**"
#     tag_matching           = "**"
#     n_days_since_last_pull = 30
#     untagged_artifacts     = false
#   }
#   rule {
#     repo_matching          = "**"
#     tag_matching           = "**"
#     n_days_since_last_push = 7
#     untagged_artifacts     = false
#   }
# }

resource "harbor_garbage_collection" "gc" {
  # run garbage collection on Sunday morning
  # try to make sure it's not run at the same time as the retention policy
  schedule        = "0 0 7 * * 0"
  delete_untagged = true
}

# registry outputs

output "registry_url" {
  value       = ovh_cloud_project_containerregistry.registry.url
  description = <<EOF
    # login to docker registry with:
    echo $(tofu output -raw registry_builder_token) | docker login $(tofu output -raw registry_url) --username $(tofu output -raw registry_builder_name) --password-stdin
    EOF
}

output "registry_admin_login" {
  value     = ovh_cloud_project_containerregistry_user.admin.login
  sensitive = true
}

output "registry_admin_password" {
  value     = ovh_cloud_project_containerregistry_user.admin.password
  sensitive = true
}


output "registry_builder_name" {
  value     = harbor_robot_account.builder.full_name
  sensitive = true
}

output "registry_builder_token" {
  value     = harbor_robot_account.builder.secret
  sensitive = true
}

output "registry_puller_name" {
  value     = harbor_robot_account.puller.full_name
  sensitive = true
}
output "registry_puller_token" {
  value     = harbor_robot_account.puller.secret
  sensitive = true
}
