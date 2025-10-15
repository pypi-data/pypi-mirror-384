from storages.backends.s3boto3 import S3Boto3Storage


class Storage(S3Boto3Storage):
    location = "media"
    custom_domain = ""
