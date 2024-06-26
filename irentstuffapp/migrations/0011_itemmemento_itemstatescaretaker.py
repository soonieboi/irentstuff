# Generated by Django 4.2.3 on 2024-04-04 03:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("irentstuffapp", "0010_rental_cancelled_date_rental_pending_date_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ItemMemento",
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
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                (
                    "condition",
                    models.CharField(
                        choices=[
                            ("excellent", "Excellent"),
                            ("good", "Good"),
                            ("fair", "Fair"),
                            ("poor", "Poor"),
                        ],
                        max_length=255,
                    ),
                ),
                ("price_per_day", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "deposit",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("image", models.ImageField(upload_to="item_images/")),
                ("created_date", models.DateTimeField()),
                ("deleted_date", models.DateTimeField(blank=True, null=True)),
                (
                    "category",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="irentstuffapp.category",
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="irentstuffapp.item",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ItemStatesCaretaker",
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
                (
                    "datetime_saved",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="caretaker",
                        to="irentstuffapp.item",
                    ),
                ),
                (
                    "memento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="irentstuffapp.itemmemento",
                    ),
                ),
            ],
        ),
    ]
