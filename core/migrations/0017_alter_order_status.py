# Generated by Django 5.0.2 on 2024-03-26 16:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_orderitems_size'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('received', 'Received'), ('order placed', 'Order Placed'), ('processing', 'Processing'), ('completed', 'Completed'), ('return', 'Return'), ('returned', 'Returned')], default='pending', max_length=20),
        ),
    ]
