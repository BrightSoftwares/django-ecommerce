# Generated by Django 3.0.10 on 2020-10-31 13:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_item_external_product_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='external_product_id',
            field=models.TextField(),
        ),
    ]
