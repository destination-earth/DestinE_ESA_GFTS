import os
import sys
from configparser import ConfigParser
from pathlib import Path
from urllib.parse import urlparse

import fs.errors
import fs.opener
from fs.info import Info, ResourceType
from fs_s3fs import S3FS
from fs_s3fs.opener import S3FSOpener

c = get_config()  # noqa

if os.getenv("CULL_TIMEOUT"):
    # shutdown the server after no activity
    c.ServerApp.shutdown_no_activity_timeout = int(os.getenv("CULL_TIMEOUT"))

if os.getenv("CULL_KERNEL_TIMEOUT"):
    # shutdown kernels after no activity
    c.MappingKernelManager.cull_idle_timeout = int(os.getenv("CULL_KERNEL_TIMEOUT"))

if os.getenv("CULL_INTERVAL"):
    # check for idle kernels this often
    c.MappingKernelManager.cull_interval = int(os.getenv("CULL_INTERVAL"))

# a kernel with open connections but no activity still counts as idle
# this is what allows us to shutdown servers when people leave a notebook open and wander off
if os.getenv("CULL_CONNECTED") not in {"", "0"}:
    c.MappingKernelManager.cull_connected = True

c.ContentsManager.hide_globs.extend(["lost+found"])


# workaround https://github.com/PyFilesystem/s3fs/issues/70
# because our files weren't created with S3FS (aka fs-s3fs)
# they were created with s3fs. Ha!


class EnsureDirS3FS(S3FS):
    def getinfo(self, path, namespaces=None):
        try:
            return super().getinfo(path, namespaces)
        except fs.errors.ResourceNotFound as e:
            # workaround https://github.com/PyFilesystem/s3fs/issues/70
            # check if it's a directory
            # if so, create it
            # scandir/getinfo don't work on missing directories
            # but listdir does
            # if it's really a directory, return stub Info
            try:
                self.listdir(path)
            except fs.errors.ResourceNotFound:
                raise e from None
            else:
                # return fake Info
                # based on getinfo handling of root (`/`)
                name = path.rstrip("/").rsplit("/", 1)[-1]
                return Info(
                    {
                        "basic": {
                            "name": name,
                            "is_dir": True,
                        },
                        "details": {"type": int(ResourceType.directory)},
                    }
                )


# define custom opener for GFTS
# loads GFTS S3 credentials from .aws/credentials [gfts] profile


class GFTSOpener(S3FSOpener):
    protocols = ["gfts-s3"]

    def open_fs(self, fs_url, parse_result, *args, **kwargs):
        bucket_name, _, dir_path = parse_result.resource.partition("/")
        creds = ConfigParser()
        creds.read(Path.home() / ".aws/credentials")
        endpoint_url = creds.get(
            "gfts",
            "aws_endpoint_url",
            fallback="https://s3.gra.perf.cloud.ovh.net",
        )
        region_name = urlparse(endpoint_url).hostname.split(".")[1]
        return EnsureDirS3FS(
            bucket_name,
            dir_path=dir_path or "/",
            aws_access_key_id=creds.get("gfts", "aws_access_key_id", fallback=None),
            aws_secret_access_key=creds.get(
                "gfts", "aws_secret_access_key", fallback=None
            ),
            endpoint_url=endpoint_url,
            region=region_name,
            acl=parse_result.params.get("acl", None),
            cache_control=parse_result.params.get("cache_control", None),
        )


fs.opener.registry.install(GFTSOpener)


c.JupyterFs.resources = fs_resources = []

bucket_env = os.environ.get("JUPYTER_FS_BUCKETS")

if bucket_env:
    buckets = bucket_env.split(",")
else:
    buckets = []

for bucket in buckets:
    url = f"gfts-s3://{bucket}/"
    try:
        with fs.open_fs(url) as s3_fs:
            list(s3_fs.scandir("/"))
    except Exception as e:
        print(f"Error listing {url}: {e}", file=sys.stderr)
        continue
    else:
        print(f"Mounting {url}", file=sys.stderr)
        fs_resources.append(
            {
                "name": bucket,
                "url": url,
            }
        )

c.ServerApp.contents_manager_class = "jupyterfs.metamanager.MetaManager"
