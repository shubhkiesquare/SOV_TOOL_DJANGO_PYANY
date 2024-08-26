# Generated by Django 3.2.25 on 2024-08-15 06:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search_app', '0006_auto_20240814_2144'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='searchquery',
            name='query',
        ),
        migrations.AlterField(
            model_name='searchquery',
            name='city',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='searchquery',
            name='country',
            field=models.CharField(choices=[('US', 'United States'), ('GB', 'United Kingdom'), ('CA', 'Canada'), ('AU', 'Australia'), ('IN', 'India')], max_length=2),
        ),
        migrations.AlterField(
            model_name='searchquery',
            name='device',
            field=models.CharField(choices=[('desktop', 'Desktop'), ('mobile', 'Mobile'), ('tablet', 'Tablet')], max_length=10),
        ),
        migrations.AlterField(
            model_name='searchquery',
            name='pagination',
            field=models.CharField(blank=True, max_length=3),
        ),
        migrations.AlterField(
            model_name='searchquery',
            name='search_engine',
            field=models.CharField(choices=[('google', 'Google Search'), ('bing', 'Bing'), ('yahoo', 'Yahoo')], max_length=10),
        ),
    ]
