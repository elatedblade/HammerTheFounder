import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Company",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                (
                    "normalized_name",
                    models.CharField(editable=False, max_length=255, unique=True),
                ),
                ("website", models.URLField(blank=True, max_length=2048)),
                ("industry", models.CharField(blank=True, max_length=120)),
                ("location", models.CharField(blank=True, max_length=255)),
                ("description", models.TextField(blank=True)),
                ("metadata_json", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ("name", "id"),
                "indexes": [models.Index(fields=("name",), name="companies_c_name_2d8260_idx")],
            },
        ),
    ]
