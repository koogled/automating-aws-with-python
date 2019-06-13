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

import boto3

import click

from bucket import BucketManager


SESSION = boto3.Session(profile_name='python-automation')
# S3 = SESSION.resource('s3')
bucket_manager = BucketManager(SESSION)


@click.group()
def cli():
    """Webotron deploys websites to AWS."""


@cli.command('list-buckets')
def list_buckets():
    """List all s3 buckets."""
    for bucket in bucket_manager.all_buckets():
        print(bucket)


@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    """List objects in an S3 bucket."""
    for obj in bucket_manager.all_objects(bucket):
        print(obj)


@cli.command('setup-bucket')
@click.argument('bucket_name')
def setup_bucket(bucket_name):
    """Create a new S3 bucket and configure."""
    # a bit of a Kludge - if regions is us-east-1,
    #  you have to leave off region info
    new_s3_bucket = bucket_manager.init_bucket(bucket_name)
    bucket_manager.set_policy(new_s3_bucket)
    bucket_manager.configure_website(new_s3_bucket)


@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket_name')
def sync(pathname, bucket_name):
    """Sync contents of PATHNAME to BUCKET."""
    bucket_manager.sync(pathname, bucket_name)


if __name__ == '__main__':
    cli()
