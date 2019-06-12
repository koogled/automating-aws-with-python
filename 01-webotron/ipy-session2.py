# coding: utf-8
import boto3
session = boto3.Session(profile_name='python-automation')
s3 = session.resource('s3')

pythonBucket = s3.create_bucket(Bucket='acg-python-automation-2', CreateBucketConfiguration={'LocationConstraint' : 'us-east-1' })

session.region_name

try:
    newBucket = s3.create_bucket(Bucket='acg-python-automation-2', CreateBucketConfiguration={'LocationConstraint' : session.region_name })
except InvalidLocationConstraint as e:
    if session.region_name == 'us-east-1':
        newBucket = s3.create_bucket(Bucket='acg-python-automation-2' )
    else:
        print( e )
except:
    print( e )

newBucket.upload_file( 'index.html', 'index.html', ExtraArgs={'ContentType' : 'text/html'} )


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
""" % newBucket.name
policy = policy.strip()
pol.put(Policy=policy)

ws = pythonBucket.Website()
ws.put(WebsiteConfiguration={'ErrorDocument': { 'Key': 'error.html'}, 'IndexDocument': {'Suffix' : 'index.html' } } )
