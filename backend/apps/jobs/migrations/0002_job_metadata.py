from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("jobs", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="job",
            name="fingerprint",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="job",
            name="first_seen_at",
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
        migrations.AddField(
            model_name="job",
            name="last_seen_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="job",
            name="metadata_json",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name="job",
            name="status",
            field=models.CharField(
                choices=[
                    ("ACTIVE", "Active"),
                    ("OPEN", "Open"),
                    ("CLOSED", "Closed"),
                    ("ARCHIVED", "Archived"),
                ],
                default="ACTIVE",
                max_length=16,
            ),
        ),
    ]
