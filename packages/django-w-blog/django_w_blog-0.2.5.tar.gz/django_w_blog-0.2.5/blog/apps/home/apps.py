"""AppConf for blog.apps.home"""

from django.apps import AppConfig


# Create your AppConf here.
class BlogHomeConfig(AppConfig):
    """App Configuration for blog.apps.home"""

    # label = "blog_home"
    name = "blog.apps.home"
    default_auto_field = "django.db.models.BigAutoField"
