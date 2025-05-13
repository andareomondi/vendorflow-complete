from django.urls import re_path
from .consumers import VendingConsumer

websocket_urlpatterns = [
    re_path(r'ws/vending/(?P<serial_number>\w+)/$', VendingConsumer.as_asgi()),
]
