"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to view= For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', view=home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import *


urlpatterns = [
    # auth endpoints
    path('api/register/', view=register, name='registration'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # images endpoints
    path('api/slides/', view=get_home_slides, name='get home slides'),
    path('api/blocks/', view=get_home_blocks, name='get home blocks'),

    # other endpoints
    # path('api/categories/', view=category_list, name='category-list'),
    # path('api/categories/<int:pk>/', view=category_detail, name='category-detail'),
    path('api/collections/', view=collection_list, name='collection list'),
    # path('api/collections/<int:pk>/', view=collection_detail, name='collection-detail'),
    path('api/products/', view=product_list, name='product list create'),
    path('api/products/<int:pk>/', view=product_detail, name='product detail'),
    path('api/search/', search_products, name='search_products'),

    path('api/add_to_wishlist_authenticated/', view=add_to_wishlist_authenticated, name='add to cart'),
    path('api/add_to_wishlist_anonymous/', view=add_to_wishlist_anonymous, name='add to cart anonymous'),
    path('api/remove_from_wishlist_authenticated/', remove_from_wishlist_authenticated, name='remove from wishlist authenticated'),
    path('api/remove_from_wishlist_anonymous/', remove_from_wishlist_anonymous, name='remove from wishlist anonymous'),
    path('api/user-wishlist/', get_user_wishlist_items, name='user wishlist items'),
    path('api/anonymous-wishlist/<str:anonymous_id>/', get_anonymous_wishlist_items, name='anonymous wishlist items'),
    path('api/check_product_in_wishlist/<int:product_id>/',check_product_in_wishlist, name='check_product_in_wishlist'),

    path('api/add-to-cart-authenticated/', add_to_cart_authenticated, name='add_to_cart_authenticated'),
    path('api/add-to-cart-anonymous/', add_to_cart_anonymous, name='add_to_cart_anonymous'),
    path('api/remove-from-cart-authenticated/', remove_from_cart_authenticated, name='remove_from_cart_authenticated'),
    path('api/remove-from-cart-anonymous/', remove_from_cart_anonymous, name='remove_from_cart_anonymous'),
    path('api/get-user-cart-items/', get_user_cart_items, name='get_user_cart_items'),
    path('api/get-anonymous-cart-items/<str:anonymous_id>/', get_anonymous_cart_items, name='get_anonymous_cart_items'),
    path('api/check-product-in-cart/<int:product_id>/', check_product_in_cart, name='check_product_in_cart'),
    path('api/create-order/', create_order, name='create order'),
    path('api/checkStatus/', checkStatus, name='check status'),
    path('api/verify-email/<str:token>/', verify_email, name='verify_email'),
    path('api/forgot-password/', resetpassword, name='reset password'),


    # path('api/genders/', view=gender_list_create, name='gender-list-create'),
    # path('api/genders/<int:pk>/', view=gender_detail, name='gender-detail'),
]
urlpatterns = [
    # auth endpoints
    path('api/register/', view=register, name='registration'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # images endpoints
    path('api/slides/', view=get_home_slides, name='get home slides'),
    path('api/blocks/', view=get_home_blocks, name='get home blocks'),

    # other endpoints
    # path('api/categories/', view=category_list, name='category-list'),
    # path('api/categories/<int:pk>/', view=category_detail, name='category-detail'),
    path('api/collections/', view=collection_list, name='collection list'),
    # path('api/collections/<int:pk>/', view=collection_detail, name='collection-detail'),
    path('api/products/', view=product_list, name='product list create'),
    path('api/products/<int:pk>/', view=product_detail, name='product detail'),
    path('api/search/', search_products, name='search_products'),

    path('api/add_to_wishlist_authenticated/', view=add_to_wishlist_authenticated, name='add to cart'),
    path('api/add_to_wishlist_anonymous/', view=add_to_wishlist_anonymous, name='add to cart anonymous'),
    path('api/remove_from_wishlist_authenticated/', remove_from_wishlist_authenticated, name='remove from wishlist authenticated'),
    path('api/remove_from_wishlist_anonymous/', remove_from_wishlist_anonymous, name='remove from wishlist anonymous'),
    path('api/user-wishlist/', get_user_wishlist_items, name='user wishlist items'),
    path('api/anonymous-wishlist/<str:anonymous_id>/', get_anonymous_wishlist_items, name='anonymous wishlist items'),
    path('api/check_product_in_wishlist/<int:product_id>/',check_product_in_wishlist, name='check_product_in_wishlist'),

    path('api/add-to-cart-authenticated/', add_to_cart_authenticated, name='add_to_cart_authenticated'),
    path('api/add-to-cart-anonymous/', add_to_cart_anonymous, name='add_to_cart_anonymous'),
    path('api/remove-from-cart-authenticated/', remove_from_cart_authenticated, name='remove_from_cart_authenticated'),
    path('api/remove-from-cart-anonymous/', remove_from_cart_anonymous, name='remove_from_cart_anonymous'),
    path('api/get-user-cart-items/', get_user_cart_items, name='get_user_cart_items'),
    path('api/get-anonymous-cart-items/<str:anonymous_id>/', get_anonymous_cart_items, name='get_anonymous_cart_items'),
    path('api/check-product-in-cart/<int:product_id>/', check_product_in_cart, name='check_product_in_cart'),
    path('api/create-order/', create_order, name='create order'),
    path('api/checkStatus/', checkStatus, name='check status'),
    path('api/verify-email/<str:token>/', verify_email, name='verify_email'),
    path('api/forgot-password/', resetpassword, name='reset password'),
    path('api/set-password/', setpassword, name='set password'),
    path('api/fetch-orders/', fetchOrders, name='fetch_orders'),
    
    # path('api/genders/', view=gender_list_create, name='gender-list-create'),
    # path('api/genders/<int:pk>/', view=gender_detail, name='gender-detail'),
]
