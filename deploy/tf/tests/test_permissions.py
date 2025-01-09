"""
Test that everyone has the right s3 permissions
"""

import json
import subprocess
import time
from itertools import chain
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import s3fs

tofu = Path(__file__).parents[1].absolute()


buckets = [
    "gfts-reference-data",
    "destine-gfts-data-lake",
    "gfts-ifremer",
    "gfts-vliz",
]

# match groups in main.tf
# currently duplicated, could get from a tofu output, but there isn't one right now
# only need one sample user from each group
groups = dict(
    s3_readonly_users="_default",
    s3_admins="minrk",
    s3_ifremer_developers="keewis",
    s3_ifremer_users="quentinmaz",
    s3_vliz_users="davidcasalsvliz",
)

all_read_buckets = ["gfts-reference-data", "destine-gfts-data-lake"]
group_write_buckets = dict(
    s3_admins=buckets,
    s3_ifremer_developers=["gfts-ifremer", "gfts-reference-data"],
    s3_ifremer_users=["gfts-ifremer"],
    s3_vliz_users=["gfts-vliz"],
)
group_read_buckets = dict()

all_users = list(chain(*groups.values()))


def tofu_output(output_name: str) -> str:
    p = subprocess.run(
        [
            "tofu",
            "output",
            "-json",
            output_name,
        ],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
        cwd=tofu,
    )
    return json.loads(p.stdout)


creds = tofu_output("s3_credentials_json")


def check_permissions(s3, bucket):
    permissions = {
        "read": False,
        "write": False,
    }

    # read: list root and read the first file
    try:
        listing = s3.listdir(bucket)
        if listing:
            first_item = listing[0]
            with TemporaryDirectory() as td:
                s3.get(first_item["Key"], Path(td) / "test")
    except PermissionError:
        pass
    else:
        permissions["read"] = True

    # write: touch a file and remove it

    test_fname = f"{bucket}/_test/{time.time()}.txt"
    try:
        s3.touch(test_fname)
    except PermissionError:
        pass
    else:
        s3.rm(test_fname)
        permissions["write"] = True
    return permissions


def make_s3(username):
    user_creds = creds[username]
    s3 = s3fs.S3FileSystem(
        anon=False,
        endpoint_url="https://s3.gra.perf.cloud.ovh.net",
        key=user_creds["aws_access_key_id"],
        secret=user_creds["aws_secret_access_key"],
    )
    return s3


def report_permissions(username):
    s3 = make_s3(username)
    for bucket in buckets:
        permissions = check_permissions(s3, bucket)
        perms = []
        for perm, has_permission in permissions.items():
            if has_permission:
                perms.append(perm)
        if not perms:
            perms = ["no"]
        print(f"{username:16} {bucket:25} {' '.join(perms)}")


@pytest.mark.parametrize("group", groups.keys())
def test_permissions(group):
    username = groups[group]
    s3 = make_s3(username)
    expected = {
        "read": set(),
        "write": set(),
    }
    expected["write"].update(group_write_buckets.get(group, []))
    expected["read"].update(all_read_buckets)
    expected["read"].update(group_read_buckets.get(group, []))
    expected["read"].update(expected["write"])

    have = {
        "read": set(),
        "write": set(),
    }
    for bucket in buckets:
        permissions = check_permissions(s3, bucket)
        if permissions["write"]:
            have["write"].add(bucket)
        if permissions["read"]:
            have["read"].add(bucket)

    assert have == expected


if __name__ == "__main__":
    # if run as a script, report everyone's permissions to the terminal
    for username in creds:
        report_permissions(username)
