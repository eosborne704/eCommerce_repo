from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome_view, name='home'),
    path('register/', views.register_user, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Store URLs
    path('stores/', views.all_stores, name='all_stores'),
    path("store/new/", views.create_store, name="create_store"),
    path("store/<int:pk>/", views.view_store, name="view_store"),
    path("store/<int:pk>/edit-store/", views.edit_store_details, name="edit_store_details"),
    path("store/<int:pk>/delete-store/", views.delete_store, name="delete_store"),

    # Product URLs
    path("store/<int:store_id>/all-products/", views.all_products, name="all_products"),
    path("store/<int:store_id>/add-product/", views.add_product, name="add_product"),
    path("product/<int:pk>/", views.view_product, name="view_product"),
    # Review URLs
    path('product/<int:product_id>/all-reviews/', views.all_reviews, name='all_reviews'),
    path("product/<int:pk>/edit/", views.edit_product_details, name="edit_product_details"),
    path("product/<int:pk>/delete/", views.delete_product, name="delete_product"),

    # Review URLs (add views as needed)
    path("product/<int:product_id>/add-review/", views.write_review, name="write_review"),
    path("review/<int:pk>/", views.view_review, name="view_review"),
    path("review/<int:pk>/edit/", views.edit_review, name="edit_review"),
    path("review/<int:pk>/delete/", views.delete_review, name="delete_review"),
    path('add-to-cart/', views.add_item_to_cart, name='add_item_to_cart'),
    path('cart/', views.show_user_cart, name='show_user_cart'),
    path('cart/empty/', views.empty_cart, name='empty_cart'),
    path('cart/checkout/', views.checkout_view, name='checkout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password_view, name='reset_password'),
]
