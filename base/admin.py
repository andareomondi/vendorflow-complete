from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Client)
admin.site.register(Machine)
admin.site.register(Transaction)
admin.site.register(Shop)
admin.site.register(Refill)
admin.site.register(RelayDevice)
admin.site.register(RelayChannel)
