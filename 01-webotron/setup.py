from setuptools import setup

setup(
    name='webotron-1962',
    version='1.0',
    author='Kane Davidson',
    author_email='not listed',
    description='Webotron 1962, is from an A Cloud Guru course and sets up a website in AWS',
    licnese='GPLv3+',
    package=['webotron'],
    url='https://github.com/koogled/automating-aws-with-python',
    install_requires=['click','boto3'],
    entry_points='''
        [console_scripts]
        webotron=webotron.webotron:cli
    '''
)
