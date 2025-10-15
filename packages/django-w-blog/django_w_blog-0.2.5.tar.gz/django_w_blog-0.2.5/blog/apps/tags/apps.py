"""AppConf for blog.apps.tags"""

from django.apps import AppConfig


# Create your config here.
class TagsConfig(AppConfig):
    """App configuration for blog.apps.tags"""

    label = "blog_tags"
    name = "blog.apps.tags"
    default_auto_field = "django.db.models.BigAutoField"
