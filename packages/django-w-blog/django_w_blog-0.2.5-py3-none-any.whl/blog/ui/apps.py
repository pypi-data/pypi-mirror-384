"""AppConf for blog.ui"""

from django.apps import AppConfig


# Create your config here.
class TheCertainNewUIConfig(AppConfig):
    """App configuration for blog.ui"""

    name = "blog.ui"
    label = "blog_ui"
    default_auto_field = "django.db.models.BigAutoField"
