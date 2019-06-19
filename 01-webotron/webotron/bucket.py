# -*- coding: utf-8 -*-
"""Classes for S3 Buckets."""

from pathlib import Path
import mimetypes
from functools import reduce

import boto3
from botocore.exceptions import ClientError

from hashlib import md5
import webotron import util


class BucketManager:
    """Manage and S3 Bucket."""

    CHUNK_SIZE = 8388608

    def __init__(self, session):
        """Create BucketManager object."""
        self.session = session
        self.s3 = self.session.resource('s3')
        self.transfer_config = boto3.s3.transfer.TransferConfig(
            multipart_chunksize=self.CHUNK_SIZE,
            multipart_threshold=self.CHUNK_SIZE
        )
        self.manifest = {}

    def get_bucket(self, bucket_name):
        """Get the bucket object using it's name."""
        return self.s3.Bucket(bucket_name)

    def get_region_name(self, bucket):
        """Get the bucket's region name."""
        bucket_location = self.s3.meta.client.get_bucket_location(
            Bucket=bucket.name)
        return bucket_location["LocationConstraint"] or 'us-east-1'

    def get_bucket_url(self, bucket):
        """Get the sebsite URL for this bucket."""
        return "http://{}.{}".format(bucket.name,
                                     util.get_endpoint(
                                        self.get_region_name(bucket)).host)

    def all_buckets(self):
        """Return all buckets."""
        return self.s3.buckets.all()

    def all_objects(self, bucket):
        """List objects in an s3 bucket."""
        return self.s3.Bucket(bucket).objects.all()

    def init_bucket(self, bucket_name):
        """Create a bucket if doesn't aready exist."""
        new_s3_bucket = None

        try:
            new_s3_bucket = self.s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': self.session.region_name
                }
            )
        except ClientError as exception:
            try:
                if(exception.response['Error']['Code'] ==
                   'InvalidLocationConstraint' and
                   self.session.region_name == 'us-east-1'):
                    new_s3_bucket = self.s3.create_bucket(Bucket=bucket_name)
                elif(exception.response['Error']['Code'] ==
                     'BucketAlreadyOwnedByYou'):
                    new_s3_bucket = self.s3.Bucket(bucket_name)
                else:
                    raise exception
            except ClientError as exception2:
                if(exception2.response['Error']['Code'] ==
                   'BucketAlreadyOwnedByYou'):
                    new_s3_bucket = self.s3.Bucket(bucket_name)
                else:
                    raise exception2
        return new_s3_bucket

    def set_policy(self, bucket):
        """Set a bucket policy to be readable by everyone."""
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
        """ % bucket.name
        policy = policy.strip()
        pol = bucket.Policy()
        pol.put(Policy=policy)

    def configure_website(self, bucket):
        """Set the default files for a bucket."""
        bucket.Website().put(
            WebsiteConfiguration={
                'ErrorDocument': {'Key': 'error.html'},
                'IndexDocument': {'Suffix': 'index.html'}
            }
        )

    def load_manifest(self, bucket):
        """Load the manifest information."""
        paginator = self.s3.meta.client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket.name):
            for obj in page.get('Contents', []):
                self.manifest[obj['Key']] = obj['ETag']

    @staticmethod
    def hash_data(data):
        """Generate md5 for data."""
        hash = md5()
        hash.update(data)
        return hash

    def get_etag(self, path):
        """Generate etag for file."""
        hashes = []

        with open(path, 'rb') as f:
            while True:
                data = f.read(self.CHUNK_SIZE)
                if not data:
                    break
                hashes.append(self.hash_data(data))
        if not hashes:
            return
        elif len(hashes) == 1:
            return '"{}"'.format(hashes[0].hexdigest())
        else:
            digests = (h.digest() for h in hashes)
            hash = self.hash_data(reduce(lambda x, y: x + y, digests))
            return '"{}-{}"'.format(hash.hexdigest(), len(hashes))

    def upload_file(self, bucket, path, key):
        """Upload path to S3_bucket at key."""
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'
        etag = self.get_etag(path)
        if self.manifest.get(key, '') == etag:
            return
        else:
            return bucket.upload_file(
                path,
                key,
                ExtraArgs={
                    'ContentType': content_type
                },
                Config=self.transfer_config
            )

    def sync(self, pathname, bucket_name):
        """Copy all of the pathname to the bucket."""
        s3_bucket = self.s3.Bucket(bucket_name)
        self.load_manifest(s3_bucket)

        root = Path(pathname).expanduser().resolve()

        def handle_directory(target):
            for pathitem in target.iterdir():
                if pathitem.is_dir():
                    handle_directory(pathitem)
    #            if p.is_file():
    #               print("path: {}\n Key: {}".format(
    #                                          pathitem,
    #                                  pathitem.relative_to(root).as_posix() ))
                if pathitem.is_file():
                    self.upload_file(
                        s3_bucket,
                        str(pathitem.as_posix()),
                        str(pathitem.relative_to(root).as_posix()))

        handle_directory(root)
