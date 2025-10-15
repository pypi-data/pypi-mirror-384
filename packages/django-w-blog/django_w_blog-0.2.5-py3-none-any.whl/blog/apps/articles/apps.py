"""AppConf for blog.apps.articles"""

from django.apps import AppConfig


# Create your AppConf here.
class BlogArticlesConfig(AppConfig):
    """App Configuration for blog.apps.articles"""

    label = "blog_articles"
    name = "blog.apps.articles"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """Register signal receivers"""

        from blog.apps.signals import register_article_signal_receivers

        register_article_signal_receivers()
