from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('speedbuild/',include("speedbuild_app.urls"))
]
