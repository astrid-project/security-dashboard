# Generated by Django 3.0.7 on 2020-06-22 19:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0009_auto_20200610_1935'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='last_modified',
            field=models.DateTimeField(),
        ),
    ]
