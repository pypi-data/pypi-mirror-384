"""Article categories model"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.api import APIField
from wagtail.models import Page
from wagtail.search import index

from blog.apps.mixins import ChildPaginatorMixin


class AbstractBlogCategory(ChildPaginatorMixin, Page):
    """Abstract model for extension"""

    description = models.CharField(
        max_length=256,
        verbose_name=_("description"),
        help_text=_("Page description"),
    )

    context_object_name = "category"
    parent_page_types = ["blog_indexes.BlogIndex"]
    subpage_types = ["blog_articles.BlogArticle"]

    api_fields = [APIField("description")]
    content_panels = Page.content_panels + [FieldPanel("description")]
    search_fields = Page.search_fields + [index.SearchField("description")]

    class Meta(Page.Meta):
        """Meta data"""

        abstract = True

    def get_ordered_children(self):
        return super().get_children().order_by("-latest_revision_created_at")


class BlogCategory(AbstractBlogCategory):
    """Blog categories"""

    template = "blog/category.html"
