from tempfile import template
from django.shortcuts import render, redirect, get_object_or_404
import json
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import *
from django.contrib import messages
from django.contrib.auth import logout
from .models import *
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
import paho.mqtt.client as mqtt
from xhtml2pdf import pisa
from io import BytesIO
from django.template.loader import render_to_string, get_template

# Create your views here.
class Home(LoginRequiredMixin, View):
    def get(self, request):
        form = ShopCreationForm  
        user = request.user
        relay_machines = RelayDevice.objects.filter(owner=user)
        shops = Shop.objects.filter(owner=user) 
        nav_links = [
            {'name': 'MarketPlace', 'url_name': 'marketplace'},
            {'name': 'Your machines', 'url_name': 'user-machine-list'},
                ]
        context = {
                'form': form,
                'shops': shops,
                'nav_links': nav_links,
                'relay': relay_machines
                } 
        return render(request, 'base/home.html', context=context)
    def post(self, request):
        form = ShopCreationForm(request.POST)
        if form.is_valid():
            shop = form.save(commit=False)
            shop.owner = request.user
            shop.save()
            messages.success(request, 'Shop created successfully')
            return redirect('home')
        return render(request, 'base/home.html', {'form': form})
def home(request):
    return redirect('home')

class ClientRegistration(View):
    def get(self, request):
       form = RegisterForm
       return render(request, 'base/register.html', {'form': form})
    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been successfully created')
            return redirect('login')
        return render(request, 'base/register.html', {'form': form})
class LogOut(View):
  def post(self, request):
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('home')

class ShopView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        shops = Shop.objects.filter(owner=user).annotate(machine_count=Count('related_shop'))
        nav_links = [
            {'name': 'MarketPlace', 'url_name': 'marketplace'},
            {'name': 'Your machines', 'url_name': 'user-machine-list'},
                ]

        if not shops:
            messages.error(request, 'Sorry, You have not registered any shop')
            return redirect('home')
        context = {
                'shops': shops,
                'nav_links': nav_links,
                }
        return render(request, 'base/shops.html', context=context)

    def post(self, request):
        form = ShopCreationForm(request.POST)
        if form.is_valid():
            shop = form.save(commit=False)
            shop.owner = request.user
            shop.save()
            messages.success(request, 'Shop created successfully')
            return redirect('home')
        return render(request, 'base/home.html', {'form': form})
class SpecificShop(LoginRequiredMixin, View):
    def get(self, request, pk):
        shop = Shop.object.get(id=pk)
        context = {
                'shop': shop
                }
        return render(request, 'base/specific_shop.html', context)
# Relay Device Views
class RelayDeviceListView(LoginRequiredMixin, View):
    def get(self, request):
        devices = RelayDevice.objects.filter(owner=request.user)
        nav_links = [
            {'name': 'MarketPlace', 'url_name': 'marketplace'},
                ]
        context = {
                'devices': devices,
                'nav_links': nav_links,
            }
        return render(request, 'relays/device_list.html', context=context)

class RelayDeviceCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = RelayDeviceForm()
        # form = ConfigureOutputsForm() 
        return render(request, 'relays/device_create.html', {'form': form})

    def post(self, request):
        form = RelayDeviceForm(request.POST)
        if form.is_valid():
            device = form.save(commit=False)
            device.owner = request.user
            device.save()
            # Create default channels
            self.create_default_channels(device)
            return redirect('relay-device-list')
        return render(request, 'relays/device_create.html', {'form': form})

    def create_default_channels(self, device):
        """Create 8 input and 8 output channels by default"""
        for channel_type in ['IN', 'OUT']:
            for i in range(1, 5):
                RelayChannel.objects.create(
                    device=device,
                    channel_type=channel_type,
                    channel_number=i,
                    state='OFF',
                    description=f"{channel_type}_{i}"
                )

class RelayDeviceDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        device = get_object_or_404(RelayDevice, pk=pk, owner=request.user)
        channels = device.channels.all().order_by('channel_type', 'channel_number')
        return render(request, 'relays/device_detail.html', {
            'device': device,
            'channels': channels
        })

class RelayChannelUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        channel = get_object_or_404(RelayChannel, pk=pk, device__owner=request.user)
        new_state = request.POST.get('state')

        if new_state in ['ON', 'OFF']:
            channel.state = new_state
            channel.save()

            # ✅ Initialize & configure MQTT client inside the view
            mqtt_client = mqtt.Client()
            mqtt_client.connect("127.0.0.1", 1883, 60)

            topic = f"relay/{channel.device.device_id}/status/"
            payload = json.dumps({
                "device_id": channel.device.device_id,
                f"{channel.channel_type}_{channel.channel_number}": new_state
            })

            mqtt_client.publish(topic, payload)  # ✅ Send MQTT message
            print(f"Published to {topic}: {payload}")

            return render(request, "relays/channel_toggle.html", {"channel": channel})

        return HttpResponse(status=400)
    def send_mqtt_command(self, channel, state):
        from .mqtt_service import mqtt_client
        topic = f"relay/{channel.device.device_id}/status/"
        print(topic)
        payload = {
            "device_id": channel.device.device_id,
            f"{channel.channel_type}_{channel.channel_number}": state
        }
        mqtt_client.client.publish(topic, json.dumps(payload))

# Transaction Views
class TransactionCreateView(LoginRequiredMixin, View):
    def get(self, request, machine_pk):
        machine = get_object_or_404(Machine, pk=machine_pk, owner=request.user)
        form = TransactionForm()
        return render(request, 'transactions/create.html', {
            'form': form,
            'machine': machine
        })

    def post(self, request, machine_pk):
        machine = get_object_or_404(Machine, pk=machine_pk, owner=request.user)
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.machine = machine
            transaction.save()
            return redirect('machine-detail', pk=machine.pk)
        return render(request, 'transactions/create.html', {
            'form': form,
            'machine': machine
        })

# Refill Views
class RefillCreateView(LoginRequiredMixin, View):
    def get(self, request, machine_pk):
        machine = get_object_or_404(Machine, pk=machine_pk, owner=request.user)
        form = RefillForm()
        return render(request, 'refills/create.html', {
            'form': form,
            'machine': machine
        })

    def post(self, request, machine_pk):
        machine = get_object_or_404(Machine, pk=machine_pk, owner=request.user)
        form = RefillForm(request.POST)
        if form.is_valid():
            refill = form.save(commit=False)
            refill.machine = machine
            refill.save()
            return redirect('machine-detail', pk=machine.pk)
        return render(request, 'refills/create.html', {
            'form': form,
            'machine': machine
        })

"""view for showing the machines
"""
class Machines(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        machines = Machine.objects.filter(owner=user, activated=True)
        paginator = Paginator(machines, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        context = {
                'machines': machines,
                'page_obj': page_obj,
                }
        return render(request, 'base/machines.html', context=context)


class Specific_Machine(LoginRequiredMixin, View):
  def get(self, request, pk):
    machine = Machine.objects.get(id=pk)
    transactions = Transaction.objects.filter(machine=machine).order_by('-date')
    refills = Refill.objects.filter(machine=machine).order_by('-date')
    context = {
      'machine': machine,
      'transactions': transactions,
      'refills': refills,
    }
    return render(request, 'base/machine_detail.html', context=context)
  def post(self, request, pk):
    machine = Machine.objects.get(id=pk)
    package = request.POST.get('packageName')
    payment_made = request.POST.get('paymentMade')
    if payment_made == 'yes':
      payment_made = True
    else:
      payment_made = False

    refill = Refill(machine=machine, token_pack=package, status='Pending', payment_made=payment_made)
    refill.save()
    messages.success(request, 'Refill request submitted successfully. Please wait for approval')
    return redirect('specific_machine', pk=pk)

"""
Views for generating each pdf report
"""
def shop_pdf_generation(request, pk):
    owner = request.user
    shop = Shop.objects.get(id=pk)
    machines = Machine.objects.filter(shop=shop)
    template = get_template('base/shop_overview.html')
    context = {
        'generation_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'owner': owner,
        'shop': shop,
        'machines': machines
    }
    html = template.render(context)

    # Create a PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('Error Rendering PDF', status=400)
