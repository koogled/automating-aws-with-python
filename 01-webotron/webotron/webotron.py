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

from webotron.bucket import BucketManager
from webotron.domain import DomainManager
from webotron.certificate import CertificateManager
from webotron.cdn import DistributionManager

import webotron import util

SESSION = None
bucket_manager = None
domain_manager = None
cert_manager = None
dist_manager = None


@click.group()
@click.option('--profile',
              default=None,
              help="Use a given AWS profile.")
def cli(profile):
    """Webotron deploys websites to AWS."""
    global SESSION, bucket_manager, domain_manager, cert_manager, dist_manager

    session_cfg = {}
    if profile:
        session_cfg['profile_name'] = profile

    SESSION = boto3.Session(**session_cfg)
    bucket_manager = BucketManager(SESSION)
    domain_manager = DomainManager(SESSION)
    cert_manager = CertificateManager(SESSION)
    dist_manager = DistributionManager(SESSION)


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
    print(bucket_manager.get_bucket_url(bucket_manager.s3.Bucket(bucket_name)))


@cli.command('setup-domain')
@click.argument('domain')
def setup_domain(domain):
    """Configure Domain to point to bucket."""
    bucket = bucket_manager.get_bucket(domain)

    zone = domain_manager.find_hosted_zone(domain) \
        or domain_manager.create_hosted_zone(domain)
    endpoint = util.get_endpoint(bucket_manager.get_region_name(bucket))
    domain_manager.create_s3_domain_record(zone, domain, endpoint)
    print("Domain configured: http://{}".format(domain))


@cli.command('find-cert')
@click.argument('domain')
def find_cert(domain):
    """Configure Domain to point to bucket."""
    print(cert_manager.find_matching_cert(domain))


@cli.command('setup-cdn')
@click.argument('domain')
@click.argument('bucket')
def setup_cdn(domain, bucket):
    """Configure CDN to point to S3 bucket."""
    dist = dist_manager.find_matching_dist(domain)

    if not dist:
        cert = cert_manager.find_matching_cert(domain)
        if not cert:  # SSL required at this time
            print('Error, no matching cert.')
            return

        dist = dist_manager.create_dist(domain, cert)
        print('Waiting for distribution deployment...')
        dist_manager.await_deploy(dist)

    zone = domain_manager.find_hosted_zone(domain) \
        or domain_manager.create_hosted_zone(domain)

    domain_manager.create_cf_domain_record(zone, domain, dist['DomainName'])
    print("Domain configured: https://{}".format(domain))

    return


if __name__ == '__main__':
    cli()
