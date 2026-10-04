
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from api.auth import ThrottledTokenObtainPairView

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('api/token', ThrottledTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify', TokenVerifyView.as_view(), name='token_verify'),
    path('api/v1/', include('api.urls')),
    # API documentation (requires login, like the API itself)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


