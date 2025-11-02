from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BalanceSheetViewSet

router = DefaultRouter()
router.register(r'balance-sheets', BalanceSheetViewSet, basename='balancesheet')

urlpatterns = [
    path('', include(router.urls)),
]

