"""Deployment script for gfts-hub

Runs helm upgrade with appropriate configuration files

Run:

    python3 deploy.py helm
"""
import os
import shlex
import subprocess
from pathlib import Path

import click

jupyterhub = Path(__file__).parent.absolute()
terraform = jupyterhub.parent / "terraform"
kube_config = jupyterhub / "secrets" / "kubeconfig.yaml"


def sh(cmd: list[str], **kwargs):
    """Run a single shell command

    wraps subprocess.run
    """
    # kwargs.setdefault("capture_output", True)
    kwargs.setdefault("check", True)
    print(f"> {shlex.join(cmd)}")
    subprocess.run(cmd, **kwargs)


def tofu_output(output_name: str) -> str:
    p = subprocess.run(
        "tofu",
        "output",
        "-raw",
        output_name,
        check=True,
        stdout=subprocess.PIPE,
        cwd=terraform,
    )
    with p:
        return p.stdout.read()


@click.group()
def cli():
    """Main entrypoint to run a deployment

    `deploy.py helm` to run a helm upgrade
    """


@cli.command()
def docker_login():
    """Run docker login to retrieve credentials for our private registry"""
    push_password = tofu_output("registry_builder_token")
    push_user = tofu_output("registry_builder_name")
    registry_url = tofu_output("registry_url")
    sh(
        [
            "docker",
            "login",
            registry_url,
            "--username",
            push_user,
            "--password-stdin",
        ],
        stdin=push_password,
    )


@cli.command()
@click.argument("chartpress_args", nargs=-1)
@click.option("--push/--no-push", default=True)
def chartpress(chartpress_args, push):
    """Run chartpress

    updates image in registry
    """
    if not chartpress_args and push:
        chartpress_args += ("--push",)
    cmd = ["chartpress", "--builder=docker-buildx", "--platform=linux/amd64"]
    cmd.extend(chartpress_args)
    sh(cmd, cwd=jupyterhub)


@cli.command()
@click.option(
    "--skip-dependency",
    is_flag=True,
    show_default=True,
    default=False,
    help="Skip `helm dependency update` for quicker repeat deployments",
)
@click.option(
    "--diff",
    is_flag=True,
    show_default=True,
    default=False,
    help="Show diff instead of deploying",
)
def helm(skip_dependency, diff):
    """Run helm to deploy updates to jupyterhub"""
    env = os.environ.copy()
    env["KUBECONFIG"] = str(kube_config)
    if not skip_dependency and not diff:
        sh(["helm", "dependency", "update", "./gfts-hub"], cwd=jupyterhub)

    helm = ["helm"]
    if diff:
        helm.extend(["diff", "--context", "3"])
    sh(
        helm
        + [
            "upgrade",
            "--install",
            "--namespace=hub",
            "hub",
            "./gfts-hub",
            "--values=config/daskhub.yaml",
            "--values=secrets/config.yaml",
        ],
        env=env,
    )


if __name__ == "__main__":
    cli()
