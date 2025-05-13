from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *

class RegisterForm(UserCreationForm):
    class Meta:
        model = Client
        fields = ['first_name', 'second_name', 'email', 'phone_number', 'address']
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Client.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
class ShopCreationForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['name', 'location'] 
class MachineForm(forms.ModelForm):
    class Meta:
        model = Machine
        fields = ['shop', 'machine_type'] 
    def __init__(self, *args, **kwargs):
        # Extract the user passed from the view
        user = kwargs.pop('owner', None)
        super().__init__(*args, **kwargs)

        # filter the shop based on the user
        if user:
            self.fields['shop'].queryset = Shop.objects.filter(owner=user)

# class RelayDeviceForm(forms.ModelForm):
#     class Meta:
#         model = RelayDevice
#         fields = ['device_id', 'name', 'is_active']
#         widgets = {
#             'device_id': forms.TextInput(attrs={'class': 'form-control'}),
#             'name': forms.TextInput(attrs={'class': 'form-control'}),
#             'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         }
#
# class RelayChannelForm(forms.ModelForm):
#     class Meta:
#         model = RelayChannel
#         fields = ['channel_type', 'channel_number', 'state', 'description']
#         widgets = {
#             'channel_type': forms.Select(attrs={'class': 'form-control'}),
#             'channel_number': forms.NumberInput(attrs={'class': 'form-control'}),
#             'state': forms.Select(attrs={'class': 'form-control'}),
#             'description': forms.TextInput(attrs={'class': 'form-control'}),
#         }
class RelayDeviceForm(forms.ModelForm):
    """This is the form for creating each relay machine"""
    class Meta:
        model = RelayDevice
        fields = ['device_id', 'name']
        widgets = {
            'device_id': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class AcquireDeviceForm(forms.Form):
    device_id = forms.CharField(widget=forms.HiddenInput())
    terms_accepted = forms.BooleanField(
        required=True,
        label="I agree to the terms and conditions",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class ConfigureOutputsForm(forms.Form):
    num_outputs = forms.IntegerField(
        min_value=1,
        max_value=32,
        label="Number of Output Channels",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter number of outputs (1-32)'
        })
    )
