"""AppConf for blog.apps.indexes"""

from django.apps import AppConfig


# Create your AppConf here.
class BlogIndexConfig(AppConfig):
    """App Configuration for blog.apps.indexes"""

    label = "blog_indexes"
    name = "blog.apps.indexes"
    default_auto_field = "django.db.models.BigAutoField"
