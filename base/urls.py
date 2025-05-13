from django.urls import path
from .views import *


urlpatterns = [
    path("home/", Home.as_view(), name="home"),
    path("user/shops/", ShopView.as_view(), name="shops"),
    path("", home),
    path("user/logout/", LogOut.as_view(), name="logout"),
    path("relays/", RelayDeviceListView.as_view(), name="relay-device-list"),
    path("relays/create/", RelayDeviceCreateView.as_view(), name="relay-device-create"),
    path(
        "relays/<int:pk>/", RelayDeviceDetailView.as_view(), name="relay-device-detail"
    ),
    path(
        "channels/<int:pk>/update/",
        RelayChannelUpdateView.as_view(),
        name="relay-channel-update",
    ),
    path("user/machines/", Machines.as_view(), name="user-machine-list"),
    path(
        "user/machines/<int:pk>/", Specific_Machine.as_view(), name="specific_machine"
    ),
]
