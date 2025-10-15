"""Home page"""

from wagtail.models import Page


class Home(Page):
    """Home page"""

    template = "blog/base.html"
    context_object_name = "home"
    parent_page_types = ["wagtailcore.Page"]
