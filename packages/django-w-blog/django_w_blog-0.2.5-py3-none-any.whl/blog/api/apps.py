"""AppConf for blog.api"""

from django.apps import AppConfig


# Create your AppConf here.
class APIConfig(AppConfig):
    """App Configuration for blog.api"""

    name = "blog.api"
    label = "blog_api"
    default_auto_field = "django.db.models.BigAutoField"
