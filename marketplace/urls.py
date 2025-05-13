from django.urls import path
from .views import *
urlpatterns = [
       path('shop/', Home.as_view(), name='marketplace'), 
       path('shop/machine/<int:pk>/', MachineCheckout.as_view(), name='machine_checkout'),
        ]
