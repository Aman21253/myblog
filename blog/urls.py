from django.urls import path
from . import views


# user : admin@myblog.com  pass : StrongPass@123
urlpatterns = [
    path("y/login/", views.y_login, name="y_login"),
    path("y/register/", views.y_register, name="y_register"),
    path("y/logout/", views.y_logout, name="y_logout"),

    path("", views.y_home, name="y_home"),

    path("y/blog/new/", views.y_blog_create, name="y_blog_create"),
    path("y/blog/<int:blog_id>/edit/", views.y_blog_edit, name="y_blog_edit"),
    path("y/blog/<int:blog_id>/delete/", views.y_blog_delete, name="y_blog_delete"),
    path("y/blog/<slug:slug>/", views.y_blog_detail, name="y_blog_detail"),

    path("y/dashboard/", views.y_dashboard, name="y_dashboard"),

    path("y/users/", views.y_users, name="y_users"),
    path("y/users/new/", views.y_user_create, name="y_user_create"),
    path("y/users/<int:user_id>/edit/", views.y_user_edit, name="y_user_edit"),
    path("y/users/<int:user_id>/delete/", views.y_user_delete, name="y_user_delete"),

    path("y/categories/", views.y_categories, name="y_categories"),
    path("y/categories/new/", views.y_category_create, name="y_category_create"),
    path("y/categories/<int:category_id>/edit/", views.y_category_edit, name="y_category_edit"),
    path("y/categories/<int:category_id>/delete/", views.y_category_delete, name="y_category_delete"),

    path("y/profile/", views.y_profile, name="y_profile"),
    path("y/profile/edit/", views.y_profile_edit, name="y_profile_edit"),


    path("y/comment/<int:comment_id>/edit/", views.y_comment_edit, name="y_comment_edit"),
    path("y/comment/<int:comment_id>/delete/", views.y_comment_delete, name="y_comment_delete"),
]