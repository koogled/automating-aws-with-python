import boto3
import click
from botocore.exceptions import ClientError
from pathlib import Path
import mimetypes

session = boto3.Session(profile_name='python-automation')
s3 = session.resource('s3')

@click.group()
def cli():
    "Webotron deployes websites to AWS"
    pass

@cli.command('list-buckets')
def list_buckets():
    "List all s3 buckets"
    for bucket in s3.buckets.all():
        print(bucket)

@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    "List objects in an s3 bucket."
    for object in s3.Bucket(bucket).objects.all():
        print(object)
    return

@cli.command('create-bucket')
@click.argument('bucket_name')
def create_bucket(bucket_name):
    "Create a new S3 bucket and configure"

    # a bit of a Kludge - if regions is us-east-1, you have to leave off region info
    try:
        newS3Bucket = s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint' : session.region_name
            }
        )
    except ClientError as e:
        try:
            if( e.response['Error']['Code'] == 'InvalidLocationConstraint' and
                     session.region_name == 'us-east-1' ):
                newS3Bucket = s3.create_bucket(Bucket=bucket_name)
            elif e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                newS3Bucket = s3.Bucket(bucket)
            else:
                raise e
        except ClientError as e2:
            if e2.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                newS3Bucket = s3.Bucket(bucket)
            else:
                raise e2

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
    """ % newS3Bucket.name
    policy = policy.strip()
    pol = newS3Bucket.Policy()
    pol.put(Policy=policy)

    ws = newS3Bucket.Website()
    ws.put(
        WebsiteConfiguration={
            'ErrorDocument': { 'Key': 'error.html'},
            'IndexDocument': {'Suffix' : 'index.html' }
        }
    )
    return

def upload_file( s3_bucket, path, key ):
    content_type = mimetypes.guess_type(key)[0] or 'text/plain'
    s3_bucket.upload_file(
        path,
        key,
        ExtraArgs={
            'ContentType':content_type
        }
    )


@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    "Sync contents of PATHNAME to BUCKET"

    s3_bucket = s3.Bucket(bucket)

    root = Path(pathname).expanduser().resolve()

    def handle_directory(target):
        for p in target.iterdir():
            if p.is_dir(): handle_directory(p)
#            if p.is_file(): print("path: {}\n Key: {}".format(p, p.relative_to(root).as_posix() ))
            if p.is_file(): upload_file( s3_bucket, str(p.as_posix()), str(p.relative_to(root).as_posix()))

    handle_directory(root)

if __name__ == '__main__':
    cli()
