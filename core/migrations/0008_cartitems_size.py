# Generated by Django 5.0.2 on 2024-03-17 10:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_cart_cartitems'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitems',
            name='size',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
    ]
