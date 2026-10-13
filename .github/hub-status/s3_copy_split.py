"""Copy objects whose key contains '//' (rclone skips them) from the GFTS S3
project to gfts-backup/s3/<bucket>/<key>. Source is only read.
Only counts are printed (the repository is public)."""
import os, sys, time
from concurrent.futures import ThreadPoolExecutor
import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config

cfg = Config(retries={"max_attempts": 10}, s3={"addressing_style": "path"}, max_pool_connections=64)
src = boto3.client("s3", endpoint_url=os.environ["SRC_ENDPOINT"], region_name="gra", config=cfg,
                   aws_access_key_id=os.environ["SRC_KEY"], aws_secret_access_key=os.environ["SRC_SECRET"])
dst = boto3.client("s3", endpoint_url=os.environ["DEST_ENDPOINT"], region_name="gra", config=cfg,
                   aws_access_key_id=os.environ["DEST_KEY"], aws_secret_access_key=os.environ["DEST_SECRET"])
DEST_BUCKET = os.environ.get("DEST_BUCKET", "gfts-backup")
tc = TransferConfig(multipart_threshold=64 << 20, multipart_chunksize=32 << 20, max_concurrency=2)


def listing(client, bucket, prefix=""):
    out = {}
    for pg in client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        for o in pg.get("Contents", []):
            out[o["Key"]] = o["Size"]
    return out


def copy_one(args):
    bucket, key = args
    for attempt in range(5):
        try:
            body = src.get_object(Bucket=bucket, Key=key)["Body"]
            dst.upload_fileobj(body, DEST_BUCKET, f"s3/{bucket}/{key}", Config=tc)
            return True
        except Exception as e:  # noqa
            print(f"retry {attempt} {type(e).__name__}", flush=True)
            time.sleep(2 ** attempt)
    return False


failed = 0
for bucket in os.environ["BUCKETS"].split():
    s = {k: v for k, v in listing(src, bucket).items() if k.startswith("/") or "//" in k}
    d = listing(dst, DEST_BUCKET, f"s3/{bucket}/")
    d = {k[len(f"s3/{bucket}/"):]: v for k, v in d.items()}
    todo = [(bucket, k) for k, v in s.items() if d.get(k) != v]
    print(f"{bucket}: {len(s)} keys with '//', {len(todo)} to copy "
          f"({sum(s[k] for _, k in todo) / 2**30:.1f} GiB)", flush=True)
    done = 0
    with ThreadPoolExecutor(32) as ex:
        for ok in ex.map(copy_one, todo):
            done += 1
            failed += not ok
            if done % 1000 == 0:
                print(f"{bucket}: {done}/{len(todo)} (failed {failed})", flush=True)
    print(f"{bucket}: finished, copied {done - failed}, failed {failed}", flush=True)
sys.exit(1 if failed else 0)
