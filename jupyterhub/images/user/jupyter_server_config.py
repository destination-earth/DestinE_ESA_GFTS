import os
from configparser import ConfigParser
from pathlib import Path
from urllib.parse import urlparse

import fs.errors
import fs.opener
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
    def getinfo(self, path, *args, **kwargs):
        try:
            return super().getinfo(path, *args, **kwargs)
        except fs.errors.ResourceNotFound as e:
            # check if getinfo failed becuase it's a directory
            # without an empty Object
            # if so, create it
            # S3FS.scandir and S3FS.getinfo don't work on missing directories
            # but S3FS.listdir does
            try:
                self.listdir(path)
            except fs.errors.ResourceNotFound:
                # it actually doesn't exist, raise original error
                raise e from None
            else:
                # it's a directory but the empty directory object doesn't exist
                # create it then call getinfo
                print(f"Making empty directory {path}")
                self.makedir(path)
                return super().getinfo(path, *args, **kwargs)


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
        # get 'gra' from 's3.gra.perf....'
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


c.JupyterFs.resources = [
    {
        "name": "gfts-data-lake",
        "url": "gfts-s3://destine-gfts-data-lake/",
    },
]

c.ServerApp.contents_manager_class = "jupyterfs.metamanager.MetaManager"
