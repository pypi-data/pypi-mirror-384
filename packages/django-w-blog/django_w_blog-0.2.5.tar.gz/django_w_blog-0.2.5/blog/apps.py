"""AppConf for blog.apps.blog"""

from django.apps import AppConfig


# Create your AppConf here.
class ArticlesConfig(AppConfig):
    """App Configuration for blog.apps.blog"""

    name = "blog.apps.blog"
    default_auto_field = "django.db.models.BigAutoField"
