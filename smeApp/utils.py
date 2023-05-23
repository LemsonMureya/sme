import os
from django.conf import settings
from PIL import Image
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html_str = template.render(context_dict)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'

    pisa_status = pisa.CreatePDF(html_str, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html_str + '</pre>')

    return response

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
