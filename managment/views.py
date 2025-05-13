from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View
from base.models import *
from base.forms import *
from django.core.paginator import Paginator
from django.urls import reverse

# Create your views here.
class Dashboard(LoginRequiredMixin, View):
    def get(self, request):
        if not request.user.is_superuser:
            messages.error(request, 'Sorry you are not allowed to access that page')
            return redirect('home')
        nav_links = [
            {'name': 'MarketPlace', 'url_name': 'marketplace'}
        ]
        users = Client.objects.all()
        paginator = Paginator(users, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            'nav_links': nav_links,
            'page_obj': page_obj,
            'users': users,
                }
        return render(request, 'managment/dashboard.html', context=context)
class ViewUser(LoginRequiredMixin, View):
    def get(self, request, pk):
        user = Client.objects.get(id=pk)
        is_user_profile = request.user == user
        relay_machines = RelayDevice.objects.filter(owner=user)
        machines = Machine.objects.filter(owner=user)
        shops = Shop.objects.filter(owner=user)
        context = {
            'user': user,
            'relay_machines': relay_machines,
            'shops': shops,
            'machines': machines,
            'is_user_profile': is_user_profile,
        }
        return render(request, 'managment/specific_user.html', context=context)
class CreateRelayDeviceView(View):
   template_name = 'managment/create_relay_device.html'
   
   def get(self, request):
       form = RelayDeviceForm()
       return render(request, self.template_name, {'form': form})
   
   def post(self, request):
       form = RelayDeviceForm(request.POST)
       if form.is_valid():
           device = form.save(commit=False)
           device.is_active = True  # Active by default in admin
           device.owner = request.user
           device.save()
           messages.success(request, f"Device {device.device_id} created successfully!")
           print('success')
           return redirect(reverse('admin_device_list'))
       return render(request, self.template_name, {'form': form})

class RelayDeviceListView(View):
    template_name = 'managment/device_list.html'
    
    def get(self, request):
        devices = RelayDevice.objects.filter(is_active=True)
        return render(request, self.template_name, {'devices': devices})
