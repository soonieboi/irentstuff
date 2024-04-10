# Generated by Django 4.2.3 on 2024-04-10 02:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import irentstuffapp.models


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
            ],
        ),
        migrations.AddField(
            model_name="item",
            name="status",
            field=models.CharField(
                choices=[
                    ("active", "Active"),
                    ("deleted", "Deleted"),
                    ("rented", "Rented"),
                ],
                default="active",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="rental",
            name="rental_rating",
            field=models.PositiveIntegerField(
                choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], null=True
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="deposit",
            field=irentstuffapp.models.PositiveDecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="price_per_day",
            field=irentstuffapp.models.PositiveDecimalField(
                decimal_places=2, max_digits=10
            ),
        ),
        migrations.AlterField(
            model_name="rental",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("confirmed", "Confirmed"),
                    ("completed", "Completed"),
                    ("cancelled", "Cancelled"),
                ],
                default="pending",
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="review",
            name="rating",
            field=models.PositiveIntegerField(
                choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], null=True
            ),
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
        migrations.AddField(
            model_name="itemmemento",
            name="item",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="irentstuffapp.item"
            ),
        ),
        migrations.AddField(
            model_name="itemmemento",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
