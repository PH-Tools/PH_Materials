# Generated by Django 5.1.3 on 2024-12-11 15:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("webportal", "0004_material_user_alter_material_unique_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="Container",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(default="assembly", max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AlterField(
            model_name="material",
            name="unique_id",
            field=models.CharField(default="c6533f", max_length=6, unique=True),
        ),
        migrations.CreateModel(
            name="Cell",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("column_number", models.IntegerField()),
                ("row_number", models.IntegerField()),
                ("value", models.TextField(blank=True, null=True)),
                (
                    "container",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cells",
                        to="webportal.container",
                    ),
                ),
            ],
        ),
    ]
