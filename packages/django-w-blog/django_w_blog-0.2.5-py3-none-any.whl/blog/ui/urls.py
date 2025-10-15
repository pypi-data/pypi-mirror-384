"""Django blog URLConf"""

from django.urls import path

from blog.ui.views import SearchView

# Create your URLConf here.
app_name = "blog"


urlpatterns = [
    path("search", SearchView.as_view(), name="search"),
]
