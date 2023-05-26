from django import template
from django.conf import settings
from PIL import Image
import os
import hashlib
import boto3
from uuid import uuid4
import io
import botocore.exceptions
import requests

register = template.Library()

@register.filter
def get_thumbnail_url(image_url):
    # Hash the image_url to create a unique thumbnail filename
    hash_object = hashlib.md5(image_url.encode())
    hex_dig = hash_object.hexdigest()
    thumbnail_key = 'thumbnails/{}.{}'.format(hex_dig, 'png')

    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_S3_REGION_NAME')
    )

    bucket_name = os.environ.get('AWS_STORAGE_BUCKET_NAME')

    # Check if the thumbnail already exists in S3
    try:
        s3.head_object(Bucket=bucket_name, Key=thumbnail_key)
        return 'https://{}.s3.amazonaws.com/{}'.format(bucket_name, thumbnail_key)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != "404":
            # Something else has gone wrong.
            raise

    # Download image from S3
    response = requests.get(image_url)
    image = Image.open(io.BytesIO(response.content))

    # Create thumbnail
    thumbnail_size = (200, 200)
    image.thumbnail(thumbnail_size)

    # Save thumbnail to a temporary file
    temp_file = io.BytesIO()
    image.save(temp_file, format='PNG')
    temp_file.seek(0)

    # Upload the thumbnail to S3 and return the new URL
    s3.upload_fileobj(
        temp_file,
        bucket_name,
        thumbnail_key,
        ExtraArgs={
            'ACL': 'public-read',
            'ContentType': 'image/png'
        }
    )

    return 'https://{}.s3.amazonaws.com/{}'.format(bucket_name, thumbnail_key)
