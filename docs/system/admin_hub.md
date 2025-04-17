# Managing access to the GFTS Hub and S3 Buckets

Only authorized users can access the GFTS Hub and its S3 buckets. The sections below explain how users can request access to the GFTS Hub, how administrators can grant access to the Hub and existing S3 buckets, and, eventually, how to create new S3 buckets when needed.

## Getting access to the GFTS Hub and S3 Buckets

The first step is to create an [issue](https://github.com/destination-earth/DestinE_ESA_GFTS/issues/new) with the following information:

1. The GitHub username of the person you want to add to the GFTS Hub;
2. The list of S3 buckets this new person would need to access.
3. If a new group of users is required, please specify the name of the new S3 private bucket to be created for this group and identify any existing users who need access to it. **A new group of users is necessary if you have a unique set of biologging data that must remain private and cannot be shared publicly, or if you need to share intermediate and non-validated results within a specific group before making them available to the GFTS community**.

:::{seealso}

The current list of authorized GFTS users can be found in [`gfts-track-reconstruction/jupyterhub/gfts-hub/values.yaml`](https://github.com/destination-earth/DestinE_ESA_GFTS/blob/main/gfts-track-reconstruction/jupyterhub/gfts-hub/values.yaml#L169).

:::

## Giving access to the GFTS Hub and existing S3 Buckets (Admin only)

Everyone can initiate a Pull Request to add a new user with read-only access to `gfts-reference-data` and `destine-gfts-data-lake`.
There is only one step:

1. Add the new user (github username) in **lowercase** in `gfts-track-reconstruction/jupyterhub/gfts-hub/values.yaml`

When the PR is merged, the github user will have read-only access to `gfts-reference-data` and `destine-gfts-data-lake` and will be able to:

```python
import s3fs
s3 = s3fs.S3FileSystem(anon=False)
s3.listdir("gfts-reference-data")
```

To grant read access to private data or write access, the user must be added to an s3 group in the `tofu` configuration,
adding the following steps which can only be done by a GFTS Hub admin:

2. Add the github username (lowercase) in one of the `s3_` groups in `gfts-track-reconstruction/jupyterhub/tofu/main.tf` for the following permissions:

   - `s3_ifremer_developers`: write access to `gfts-ifremer` and `gfts-reference-data`
   - `s3_ifremer_users`: write access to `gfts-ifremer` only
   - `s3_vliz_users`: write access to `gfts-vliz` only
   - `s3_admins`: admin access to all s3 buckets

   If you need to create a new user group and a private S3 bucket for them, please read the next section on creating a new user group before proceeding with steps 3–6.

3. Run `tofu apply` to apply the S3 permissions. Ensure you are in the `gfts-track-reconstruction/jupyterhub/tofu` folder before executing the `tofu` command and have run `source secrets/ovh-creds.sh`.
4. Update `gfts-track-reconstruction/jupyterhub/secrets/config.yaml` with the output of the command `tofu output -json s3_credentials_json`. This command needs to be executed in the `tofu` folder after applying the S3 permissions with `tofu apply`. If the file contains binary content, it means you do not have the rights to add new users to the GFTS S3 buckets and will need to ask a GFTS admin for assistance.
5. Run `pytest` in the `tofu` directory to test s3 permissions.
6. Don't forget to commit and push your changes!

Steps 3 and 4 are what actually grant the jupyterhub user s3 access.

## Creating a new group of users (Admin only)

If you need to create a new user group with a corresponding private S3 bucket, follow the additional step below (to be completed after step 1 and before step 2).

Choose a new group name (not too long e.g. < 8 characters) which can be the organisation name of the user(s) or its acronym. We suggest to add the prefix `gfts-` (e.g. gfts-ifremer, gfts-vliz, etc.). In the example below, we are adding a new group of users called `gfts-vliz`:

- Add the new bucket name in the `s3_buckets` variable in `gfts-track-reconstruction/jupyterhub/tofu/main.tf`:

```
  s3_buckets = toset([
    "gfts-vliz",
    "gfts-ifremer",
    "gfts-reference-data",
    "destine-gfts-data-lake",
  ])
```

- Create a new variable to list the users who will have access to the new S3 bucket. Locate the variable `s3_ifremer_users` and add the new variable immediately after it:

```
  s3_vliz_users = toset([
    "davidcasalsvliz",
  ])
```

- Update the `s3_users` variable by adding the new list of users (here `local.s3_vliz_users`):

```
s3_users = setunion(local.s3_readonly_users, local.s3_admins, local.s3_vliz_users, local.s3_ifremer_developers, local.s3_ifremer_users)
```

- Create a new resource policy for this new group of users (search for `resource "ovh_cloud_project_user_s3_policy" "s3_ifremer_users"` to locate the section on resource policy for users):

```
resource "ovh_cloud_project_user_s3_policy" "s3_vliz_users" {
  for_each     = local.s3_vliz_users
  service_name = local.service_name
  user_id      = ovh_cloud_project_user.s3_users[each.key].id
  policy = jsonencode({
    "Statement" : concat([
      {
        "Sid" : "Admin",
        "Effect" : "Allow",
        "Action" : local.s3_admin_action,
        "Resource" : [
          "arn:aws:s3:::${aws_s3_bucket.gfts-vliz.id}",
          "arn:aws:s3:::${aws_s3_bucket.gfts-vliz.id}/*",
        ]
      },
    ], local.s3_default_policy)
  })
}
```

Make sure your replace `vliz` with the new group name!

- Create the new S3 bucket by locating resource `"aws_s3_bucket" "gfts-ifremer"` and adding the new bucket configuration immediately after it:

```
resource "aws_s3_bucket" "gfts-vliz" {
  bucket = "gfts-vliz"
}
```

- You are done with the configuration of the new group and its corresponding private S3 bucket. Go back to the previous section on [giving access to the GFTS Hub and S3 buckets](https://destination-earth.github.io/DestinE_ESA_GFTS/admin_hub.html#giving-access-to-the-gfts-hub-and-s3-buckets-admin-only) and follow the steps 2-6.

:::{caution}

The following packages need to be installed on your system:

1. [ssh-vault](https://ssh-vault.com);
2. [git-crypt](https://github.com/AGWA/git-crypt/blob/master/INSTALL.md);
3. [opentofu](https://opentofu.org)

As an admin, you'll need to set up your environment. The GFTS maintainer will provide you with a key encrypted with your GitHub SSH key. Save the content sent by the GFTS maintainer into a file, and name it `ssh-vault.txt`. At the moment, the keys are known to [annefou](https://github.com/annefou) and [minrk](https://github.com/minrk).

```bash
cat ssh-vault.txt | ssh-vault view | base64 --decode > keyfile && git-crypt unlock keyfile && rm keyfile
```

Before executing the command above, ensure you have changed the directory to the root of the `DestinE_ESA_GFTS` git repository.

Thanks to the previous command, you should be able to `cat gfts-track-reconstruction/jupyterhub/tofu/secrets/ovh-creds.sh` and see a text file.

Finally to initialize your environment and execute `tofu` commands, you need to change the directory to the `gfts-track-reconstruction/jupyterhub/tofu` folder and source `secrets/ovh-creds.sh` e.g.:

```bash
source secrets/ovh-creds.sh
tofu init
tofu apply
```

:::

Then you are ready to go and can follow the steps explained above to grant access to S3 buckets to a new user.
