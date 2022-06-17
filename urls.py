from .views import *
from django.urls import path
from .core.urls import urlpatterns as default_patterns

urlpatterns = [
    # Add your admin urls here
] + default_patterns