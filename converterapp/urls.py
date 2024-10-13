"""converterapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from mainapps.accounts.views import CustomUserCreateSerializer
from mainapps.accounts.views import  CustomUserViewSet

router = DefaultRouter()
router.register(r'users', CustomUserViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', include('convert.urls')),
    path('accounts/', include('mainapps.accounts.urls', namespace='accounts')),
    path('', include('mainapps.home.urls', namespace='home')),
    path('video/', include('mainapps.video.urls', namespace='video')),
    path('text/', include('mainapps.vidoe_text.urls', namespace='video_text')),
    path("stripe/", include("djstripe.urls", namespace="djstripe")),
    path("auth/", include("django.contrib.auth.urls")),
    re_path(r"^auth/", include("djoser.urls")),
    re_path(r"^auth/", include("djoser.urls.authtoken")),
    path("payments/", include("mainapps.payment.urls")),
]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
