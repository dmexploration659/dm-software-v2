from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EdtwViewSet

router = DefaultRouter()
router.register('edtwExampleAPI', EdtwViewSet, basename='edtwExampleAPI')

urlpatterns = [
    path('', include(router.urls)),
]
