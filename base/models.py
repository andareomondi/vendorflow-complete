from datetime import datetime
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
# my models 
class ClientUserManager(BaseUserManager):
    def create_user(self, first_name, second_name, email, phone_number, password=None, address=None):
        if not email:
            raise ValueError('User should have an email')
        if not phone_number:
            raise ValueError('User should have an phone_number')
        user = self.model(
            first_name=first_name,
            second_name=second_name,
            email = email,
            phone_number=phone_number,
            address=address,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, first_name, second_name, email, phone_number, password=None, address=None):
        user = self.create_user(
            first_name=first_name,
            second_name=second_name,
            email=email,
            phone_number=phone_number,
            password=password,
            address=address,
        )
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)

class Client(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=255)
    second_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, max_length=255)
    phone_number = models.IntegerField()
    created_on = models.DateTimeField(auto_now_add=True)
    address = models.CharField(blank=True, null=True, max_length=255, default='Jamcity')
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = ClientUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'second_name', 'phone_number', 'address']

    def __str__(self):
        return f'{self.first_name} {self.second_name}'

class Shop(models.Model):
    name = models.CharField(max_length=255)
    total_sales = models.PositiveIntegerField(default=0)
    amount = models.PositiveIntegerField(default=0)
    customers_served = models.PositiveIntegerField(default=0)
    location = models.CharField(max_length=255, default='Kitengela')
    owner = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='owning')

    def __str__(self):
        return self.name

class Machine(models.Model):
    CHOICES = [
        ('Milk', 'Milk'),
        ('Juice', 'Juice'),
        ('Cooking oil', 'Cooking oil'),
        ('Other', 'Other'),
    ]
    serial_number = models.CharField(max_length=255, unique=True)
    machine_type = models.CharField(max_length=255, choices=CHOICES, default='Milk')
    total_volume = models.FloatField(default=0.000)
    total_amount = models.FloatField(default=0.000)
    initial_tokens = models.PositiveIntegerField(default=15)  # Updated to 15 tokens
    remaining_tokens = models.PositiveIntegerField(default=15)  # Updated to 15 tokens
    days_used = models.PositiveIntegerField(default=0)
    cost_per_day = models.FloatField(default=3.0)  # Each day costs 3 Ksh
    tokens_per_month = models.PositiveIntegerField(default=30)
    owner = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='vending_machine')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='related_shop', blank=True, null=True)
    last_processed_date = models.DateField(default=datetime.now)
    activated = models.BooleanField(default=False)
    price = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f'{self.serial_number}'

    def process_daily_usage(self):
        current_date = datetime.now().date()
        if (current_date - self.last_processed_date).days >= 1:
            self.days_used += 1
            self.total_amount += self.cost_per_day
            self.remaining_tokens -= 1  # One token per day
            self.last_processed_date = current_date
            self.save()


class Transaction(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='transactions')
    amount = models.FloatField(default=0.000)
    date = models.DateTimeField(auto_now_add=True)
    volume = models.FloatField(default=0.000)
    token_used = models.FloatField(default=1)
    total_amount = models.FloatField(default=0.000)
    total_volume = models.FloatField(default=0.000)

    def __str__(self):
        return f'{self.machine.serial_number} - {self.date} - {self.amount}'

    def remaining_tokens(self):
        self.machine.total_amount = self.total_amount
        self.machine.total_volume = self.total_volume
        self.machine.remaining_tokens = self.machine.initial_tokens - self.token_used
        self.machine.save()
        return True

class Refill(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='refills')
    date = models.DateTimeField(auto_now_add=True)
    payment_made = models.BooleanField(default=False)
    status = models.CharField(max_length=100, default='Pending')
    token_pack = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.machine.serial_number} - {self.date}'

    def refill_tokens(self):
        if self.payment_made and self.status == 'Approved':
            if self.token_pack == 'Starter Pack':
                self.machine.remaining_tokens += 25
                self.machine.save()
            elif self.token_pack == 'Popular Pack':
                self.machine.remaining_tokens += 50
                self.machine.save()
            elif self.token_pack == 'Bulk Pack':
                self.machine.remaining_tokens += 100
                self.machine.save()

class RelayDevice(models.Model):
    """Model representing an IoT relay controller device"""
    device_id = models.CharField(
        max_length=24, 
        unique=True,
        help_text="Unique identifier for the device (e.g., 0677FF565165854967054030)"
    )
    name = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Human-readable name for the device"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='relay_owner')
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.device_id})" if self.name else self.device_id


class RelayChannel(models.Model):
    """Model representing a single channel (input or output) on a relay device"""
    CHANNEL_TYPES = [
        ('IN', 'Input'),
        ('OUT', 'Output'),
    ]
    
    STATES = [
        ('ON', 'On'),
        ('OFF', 'Off'),
    ]

    device = models.ForeignKey(
        RelayDevice, 
        on_delete=models.CASCADE,
        related_name='channels'
    )
    channel_type = models.CharField(
        max_length=3, 
        choices=CHANNEL_TYPES
    )
    channel_number = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(32)  # Assuming max 32 channels per device
        ]
    )
    state = models.CharField(
        max_length=3, 
        choices=STATES, 
        default='OFF'
    )
    last_updated = models.DateTimeField(auto_now=True)
    description = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Description of what this channel controls"
    )

    class Meta:
        unique_together = [('device', 'channel_type', 'channel_number')]
        ordering = ['device', 'channel_type', 'channel_number']

    def __str__(self):
        return f"{self.device} {self.channel_type}_{self.channel_number} ({self.state})"
