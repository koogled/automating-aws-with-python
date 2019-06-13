#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Webotron: Deploy webistes with aws.

Webotron automates the process of deploying static websites to AWS.
- Configure AWS S3 list_buckets
  - Create them
  - Set them up for static website hosting
  - Deploy local files

- Configure DNS with AWS Route 53
- Configure Content Deliver Network and SSL with AWS CloudFront
"""

from pathlib import Path
import mimetypes

import boto3
from botocore.exceptions import ClientError
import click

SESSION = boto3.Session(profile_name='python-automation')
S3 = SESSION.resource('s3')


@click.group()
def cli():
    """Webotron deploys websites to AWS."""


@cli.command('list-buckets')
def list_buckets():
    """List all s3 buckets."""
    for bucket in S3.buckets.all():
        print(bucket)


@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    """List objects in an S3 bucket."""
    for obj in S3.Bucket(bucket).objects.all():
        print(obj)


@cli.command('create-bucket')
@click.argument('bucket_name')
def create_bucket(bucket_name):
    """Create a new S3 bucket and configure."""
    # a bit of a Kludge - if regions is us-east-1,
    #  you have to leave off region info
    try:
        new_s3_bucket = S3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint': SESSION.region_name
            }
        )
    except ClientError as exception:
        try:
            if(exception.response['Error']['Code'] ==
               'InvalidLocationConstraint' and
               SESSION.region_name == 'us-east-1'):
                new_s3_bucket = S3.create_bucket(Bucket=bucket_name)
            elif(exception.response['Error']['Code'] ==
                 'BucketAlreadyOwnedByYou'):
                new_s3_bucket = S3.Bucket(bucket_name)
            else:
                raise exception
        except ClientError as exception2:
            if(exception2.response['Error']['Code'] ==
               'BucketAlreadyOwnedByYou'):
                new_s3_bucket = S3.Bucket(bucket_name)
            else:
                raise exception2

    policy = """
    {
      "Version":"2012-10-17",
      "Statement":[{
      "Sid":"PublicReadGetObject",
      "Effect":"Allow",
      "Principal": "*",
      "Action":["s3:GetObject"],
      "Resource":["arn:aws:s3:::%s/*"
          ]
        }
      ]
    }
    """ % new_s3_bucket.name
    policy = policy.strip()
    pol = new_s3_bucket.Policy()
    pol.put(Policy=policy)

    website = new_s3_bucket.Website()
    website.put(
        WebsiteConfiguration={
            'ErrorDocument': {'Key': 'error.html'},
            'IndexDocument': {'Suffix': 'index.html'}
        }
    )


def upload_file(s3_bucket, path, key):
    """Upload path to S3_bucket at key."""
    content_type = mimetypes.guess_type(key)[0] or 'text/plain'
    s3_bucket.upload_file(
        path,
        key,
        ExtraArgs={
            'ContentType': content_type
        }
    )


@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    """Sync contents of PATHNAME to BUCKET."""
    s3_bucket = S3.Bucket(bucket)

    root = Path(pathname).expanduser().resolve()

    def handle_directory(target):
        for pathitem in target.iterdir():
            if pathitem.is_dir():
                handle_directory(pathitem)
#            if p.is_file():
#               print("path: {}\n Key: {}".format(
#                                          pathitem,
#                                      pathitem.relative_to(root).as_posix() ))
            if pathitem.is_file():
                upload_file(
                    s3_bucket,
                    str(pathitem.as_posix()),
                    str(pathitem.relative_to(root).as_posix()))

    handle_directory(root)


if __name__ == '__main__':
    cli()
