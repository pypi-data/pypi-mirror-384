"""AppConf for blog.cms"""

from django.apps import AppConfig


# Create your config here.
class CMSConfig(AppConfig):
    """App configuration for blog.cms"""

    name = "blog.cms"
    label = "blog_cms"
    default_auto_field = "django.db.models.BigAutoField"
