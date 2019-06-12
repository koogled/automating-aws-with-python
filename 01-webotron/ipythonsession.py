# coding: utf-8
import boto3
session = boto3.Session(profile_name='python-automation')
s3 = session.resource('s3')

for bucket in s3.buckets.all():
    print(bucket)


#pythonBucket = s3.create_bucket(Bucket='acg-python-automation')
#for bucket in s3.buckets.all():
#    print(bucket)
