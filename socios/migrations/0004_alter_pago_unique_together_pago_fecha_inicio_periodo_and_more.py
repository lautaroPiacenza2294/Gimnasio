# Generated by Django 5.2.3 on 2025-07-12 16:32

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('socios', '0003_alter_ingreso_options_alter_pago_options_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='pago',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='pago',
            name='fecha_inicio_periodo',
            field=models.DateField(default=datetime.date(2025, 7, 12), help_text='Cuándo inicia el período pagado'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pago',
            name='fecha_vencimiento_periodo',
            field=models.DateField(default=datetime.date(2025, 8, 11), help_text='Cuándo vence el período pagado'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='pago',
            name='fecha_pago',
            field=models.DateField(auto_now_add=True, help_text='Cuándo se registró el pago'),
        ),
        migrations.AlterField(
            model_name='pago',
            name='mes_correspondiente',
            field=models.DateField(blank=True, help_text='Campo legacy - usar fecha_inicio_periodo', null=True),
        ),
    ]
