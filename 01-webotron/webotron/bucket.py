# -*- coding: utf-8 -*-
"""Classes for S3 Buckets."""

import mimetypes
from pathlib import Path
from botocore.exceptions import ClientError


class BucketManager:
    """Manage and S3 Bucket."""

    def __init__(self, session):
        """Create BucketManager object."""
        self.session = session
        self.s3 = self.session.resource('s3')

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

    @staticmethod
    def upload_file(bucket, path, key):
        """Upload path to S3_bucket at key."""
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'
        return bucket.upload_file(
            path,
            key,
            ExtraArgs={
                'ContentType': content_type
            }
        )

    def sync(self, pathname, bucket_name):
        """Copy all of the pathname to the bucket."""
        s3_bucket = self.s3.Bucket(bucket_name)

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
