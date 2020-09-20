# Generated by Django 3.0.9 on 2020-09-20 13:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_auto_20200920_1212'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=256, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='order',
            name='payment',
        ),
        migrations.AddField(
            model_name='payment',
            name='order',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='payments', related_query_name='orderpayment', to='core.Order'),
        ),
        migrations.AddField(
            model_name='payment',
            name='status',
            field=models.CharField(choices=[('N', 'New, waiting for payment'), ('P', 'Paid'), ('F', 'Payment failed')], default='N', max_length=1),
        ),
        migrations.AddField(
            model_name='payment',
            name='payment_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.PaymentType'),
        ),
    ]
