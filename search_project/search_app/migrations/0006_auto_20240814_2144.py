# Generated by Django 3.2.25 on 2024-08-14 16:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search_app', '0005_auto_20240814_1520'),
    ]

    operations = [
        migrations.AlterField(
            model_name='searchquery',
            name='end_date',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='searchquery',
            name='start_date',
            field=models.DateTimeField(),
        ),
    ]
