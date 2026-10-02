import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("companies", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Job",
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
                ("external_source", models.CharField(max_length=100)),
                ("external_id", models.CharField(max_length=255)),
                ("canonical_url", models.URLField(blank=True, max_length=2048)),
                ("title", models.CharField(max_length=300)),
                ("location", models.CharField(blank=True, max_length=255)),
                ("employment_type", models.CharField(blank=True, max_length=64)),
                ("description", models.TextField(blank=True)),
                ("status", models.CharField(default="ACTIVE", max_length=32)),
                ("fingerprint", models.CharField(blank=True, max_length=128)),
                ("first_seen_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen_at", models.DateTimeField(auto_now=True)),
                ("metadata_json", models.JSONField(default=dict)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="jobs",
                        to="companies.company",
                    ),
                ),
            ],
            options={
                "ordering": ("-last_seen_at", "-id"),
                "indexes": [
                    models.Index(
                        fields=("company", "status"), name="jobs_job_company_797da4_idx"
                    ),
                    models.Index(
                        fields=("external_source", "external_id"),
                        name="jobs_job_externa_21ea8d_idx",
                    ),
                    models.Index(fields=("fingerprint",), name="jobs_job_fingerp_deaa65_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("external_source", "external_id"),
                        name="jobs_external_source_id_unique",
                    ),
                ],
            },
        ),
    ]
