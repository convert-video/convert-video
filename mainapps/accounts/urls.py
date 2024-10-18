from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views
from mainapps.accounts.views import change_password
app_name='accounts'
urlpatterns=[
    path('login/',login,name='signin'),
    path('pricing/',embedded_pricing_page,name='embedded_pricing_page'),
    path('confirm-subscription/',subscription_confirm,name='subscription_confirm'),
    path('logout/', logout_view, name='logout'),  
    path('profile/', subscription_details, name='subscription_details'),
    path('change-password/', change_password, name='change-password'),
]


# 4242 4242 4242 4242