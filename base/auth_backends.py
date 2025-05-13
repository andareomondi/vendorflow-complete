# base/auth_backends.py
from django.contrib.auth.backends import BaseBackend
from .models import Client

class AuthBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None):
        # Your custom authentication logic here
        try:
            client = Client.objects.get(email=email)
            if client.check_password(password):
                return client
        except Client.DoesNotExist:
            return None
    def get_user(self, user_id):
        try:
            return Client.objects.get(pk=user_id)
        except Client.DoesNotExist:
            return None
