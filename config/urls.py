# config/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('posts.urls')),        # 게시물 관련 URL, '/'(root)에 매핑
    path('users/', include('users.urls')),  # 사용자 관련 URL, '/users/'에 매핑
    path('links/', include('links.urls')),  # 링크 관련 URL, '/links/'에 매핑
]

# 개발 환경에서 미디어 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
