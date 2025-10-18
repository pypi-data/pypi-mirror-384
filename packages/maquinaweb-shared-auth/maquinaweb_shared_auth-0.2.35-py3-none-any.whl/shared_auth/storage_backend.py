from storages.backends.s3boto3 import S3Boto3Storage
from .conf import CUSTOM_DOMAIN_AUTH

class Storage(S3Boto3Storage):
    location = "media"
    custom_domain = CUSTOM_DOMAIN_AUTH
