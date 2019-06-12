import boto3
import click

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

if __name__ == '__main__':
    cli()
