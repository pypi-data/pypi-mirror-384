"""blog articles"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.contrib.taggit import ClusterTaggableManager
from wagtail.admin.panels import FieldPanel
from wagtail.api import APIField
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index
from wagtail.images import get_image_model

from blog.cms.blocks import AllBlocks


Image = get_image_model()


# Create your models here.
class AbstractBlogArticle(Page):
    """Abstract model for extension"""

    image = models.ForeignKey(
        Image,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("image"),
        help_text=_("Article image"),
    )
    headline = models.CharField(
        max_length=256,
        verbose_name=_("headline"),
        help_text=_("Article headline"),
    )
    content = StreamField(
        AllBlocks(),
        verbose_name=_("content"),
        help_text=_("Article content"),
    )
    tags = ClusterTaggableManager(
        blank=True,
        through="blog_tags.Tag",
        verbose_name=_("tags"),
        help_text=_("Tags"),
    )

    context_object_name = "article"
    parent_page_types = ["blog_categories.BlogCategory"]
    subpage_types = []

    api_fields = [
        APIField("image"),
        APIField("headline"),
        APIField("content"),
        APIField("tags"),
    ]
    content_panels = Page.content_panels + [
        FieldPanel("image"),
        FieldPanel("headline"),
        FieldPanel("content"),
        FieldPanel("tags"),
    ]
    search_fields = Page.search_fields + [
        index.SearchField("image"),
        index.SearchField("headline"),
        index.SearchField("content"),
        index.FilterField("tags"),
    ]

    def get_ordered_siblings(self, inclusive=False):
        return super().get_siblings(inclusive).order_by("-latest_revision_created_at")

    class Meta(Page.Meta):
        """Meta data"""

        abstract = True
        verbose_name = _("blog articles")
        verbose_name_plural = _("blog articles")


class BlogArticle(AbstractBlogArticle):
    """blog articles"""

    template = "blog/article.html"
