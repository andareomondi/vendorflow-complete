from django.urls import path
from .views import *
urlpatterns = [
    path('dashboard/', Dashboard.as_view(), name='admin-dashboard'),
    path('relay-devices/create/', CreateRelayDeviceView.as_view(), name='create_relay_device'),
    path('relay-devices/', RelayDeviceListView.as_view(), name='admin_device_list'),
        ]
