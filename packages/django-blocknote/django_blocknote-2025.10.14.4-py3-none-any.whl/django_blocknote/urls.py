from django.urls import path

from django_blocknote.views import (
    remove_image,
    upload_file,
    upload_image,
)

app_name = "django_blocknote"
app_label = "django_blocknote"

urlpatterns = [
    path(
        "upload-image/",
        upload_image,
        name="upload_image",
    ),
    path(
        "remove-image/",
        remove_image,
        name="remove_image",
    ),
    path(
        "upload-file/",
        upload_file,
        name="upload_file",
    ),
]
