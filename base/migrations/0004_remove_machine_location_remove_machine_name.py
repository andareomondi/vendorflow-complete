# Generated by Django 5.1.7 on 2025-03-25 05:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_machine_price'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='machine',
            name='location',
        ),
        migrations.RemoveField(
            model_name='machine',
            name='name',
        ),
    ]
