from base.forms import * 
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from base.models import Machine, Shop
from django.core.paginator import Paginator
from django.contrib import messages
# Create your views here.
class Home(LoginRequiredMixin, View):
    def get(self, request):
       machines = Machine.objects.filter(activated=False) 
       nav_links = [
            {'name': 'MarketPlace', 'url_name': 'marketplace'},
                ]
       if not machines:
          messages.success(request, 'Sorry there are no available machines for sale') 
          return redirect('home')
       devices = machines 
       paginator = Paginator(devices, 10)
       page_number = request.GET.get("page")
       page_obj = paginator.get_page(page_number)
       context = {
            'machines': machines,
            'page_obj': page_obj,
            'nav_links': nav_links,
        }
       return render(request, 'marketplace/home.html', context=context)
class MachineCheckout(LoginRequiredMixin, View):
    def get(self, request, pk):
        user_shops = Shop.objects.filter(owner=request.user)
        if not user_shops.exists():
            messages.error(request, 'Machine activation requires you to have a already registered shop.')
            return redirect('home')
        machine = Machine.objects.get(id=pk)
        form = MachineForm(owner=request.user, instance=machine)
        context = {
                'machine': machine,
                'form': form,
                }
        return render(request, 'marketplace/machine_checkout.html', context=context)
    def post(self, request):
        form = MachineForm(request.POST)
        if form.is_valid():
            machine = form.save(commit=False)
            machine.owner = request.user
            machine.activated = True
            machine.save()
            messages.success(request, 'Machine Activated success')
            return redirect('home')
