from django import template
from django.conf import settings
from PIL import Image
import os

register = template.Library()

@register.filter
def get_thumbnail_url(image_url):
    file_path = os.path.join(settings.MEDIA_ROOT, image_url.replace(settings.MEDIA_URL, ""))

    # Create thumbnail
    image = Image.open(file_path)
    thumbnail_size = (200, 200)
    image.thumbnail(thumbnail_size)

    # Save thumbnail
    thumbnail_filename = os.path.splitext(file_path)[0] + "_thumbnail" + os.path.splitext(file_path)[1]
    image.save(thumbnail_filename)

    # Return the thumbnail URL
    thumbnail_url = os.path.join(settings.MEDIA_URL, os.path.relpath(thumbnail_filename, settings.MEDIA_ROOT)).replace("\\", "/")
    return thumbnail_url
