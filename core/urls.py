from django.urls import path
from django.views.generic import TemplateView
from .views import (
    FileUploadView,
    ProcessFileView,
    DownloadFileView,
    GeneratePlotView,
)

urlpatterns = [
    # Frontend page
    path("", TemplateView.as_view(template_name="core/index.html"), name="index"),

    # API endpoints
    path("upload/", FileUploadView.as_view(), name="file-upload"),
    path("process/", ProcessFileView.as_view(), name="file-process"),
    path("download/", DownloadFileView.as_view(), name="file-download"),
    path("plot/", GeneratePlotView.as_view(), name="file-plot"),
]
