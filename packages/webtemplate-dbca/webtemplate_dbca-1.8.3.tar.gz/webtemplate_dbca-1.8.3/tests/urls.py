from django.urls import path

from tests import views

urlpatterns = [
    path("test-b4/", views.TestB4Page.as_view(), name="test_page_b4"),
    path("test-b5/", views.TestB5Page.as_view(), name="test_page_b5"),
    path("test2/", views.TestPage2.as_view(), name="test_page_2"),
    # We need the following named URLs to render the base template.
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
]
