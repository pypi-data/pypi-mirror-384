"""blog Index page"""

from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.api import APIField
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index

from blog.apps.articles.models import BlogArticle
from blog.cms.blocks import MediaBlock


# Create your models here.
class AbstractBlogIndex(Page):
    """Abstract model for extension"""

    content = StreamField(
        MediaBlock(),
        verbose_name=_("content"),
        help_text=_("Page content"),
    )

    context_object_name = "index"
    parent_page_types = ["home.Home"]
    subpage_types = ["blog_categories.BLogCategory"]

    api_fields = [APIField("content")]
    content_panels = Page.content_panels + [FieldPanel("content")]
    search_fields = Page.search_fields + [index.SearchField("content")]

    class Meta(Page.Meta):
        """Meta data"""

        abstract = True

    def get_context(self, request, *args, **kwargs):
        """Add latest articles to context"""

        context = super().get_context(request, *args, **kwargs)

        return {
            **context,
            "articles": self.get_descendants()
            .type(BlogArticle)
            .live()
            .order_by("-latest_revision_created_at")
            .specific(),
        }


class BlogIndex(AbstractBlogIndex):
    """blog index pages"""

    template = "blog/index.html"
