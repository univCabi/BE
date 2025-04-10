# Generated by Django 5.1.1 on 2025-04-06 23:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cabinet', '0002_alter_cabinets_building_id_alter_cabinets_reason_and_more'),
        ('user', '0002_alter_users_building_id_delete_buildings'),
    ]

    operations = [
        migrations.CreateModel(
            name='cabinet_bookmarks',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('cabinet_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cabinet.cabinets')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.users')),
            ],
        ),
    ]
