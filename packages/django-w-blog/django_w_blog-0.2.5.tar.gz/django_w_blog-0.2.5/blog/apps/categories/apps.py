"""AppConf for blog.apps.categories"""

from django.apps import AppConfig


# Create your AppConf here.
class BlogCategoriesConfig(AppConfig):
    """App Configuration for blog.apps.categories"""

    label = "blog_categories"
    name = "blog.apps.categories"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """Register signal receivers"""

        from blog.apps.signals import register_category_signal_receivers

        register_category_signal_receivers()
