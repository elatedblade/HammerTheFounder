from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = [("users", "0001_initial"), ("campaigns", "0002_campaign_assigned_to")]
    operations = [migrations.CreateModel(name="Inquiry", fields=[
        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
        ("plan", models.CharField(choices=[("NORMAL_APPLY", "Normal Apply"), ("COLD_APPLY", "Cold Apply"), ("FULL_THROTTLE", "Full-Throttle Sprint")], max_length=20)),
        ("status", models.CharField(choices=[("OPEN", "Open"), ("CONTACTED", "Contacted"), ("CONVERTED", "Converted"), ("CLOSED", "Closed")], default="OPEN", max_length=12)),
        ("reference", models.CharField(editable=False, max_length=40, unique=True)),
        ("notes", models.TextField(blank=True, max_length=10000)),
        ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
        ("campaign", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="source_inquiries", to="campaigns.campaign")),
        ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="inquiries", to=settings.AUTH_USER_MODEL)),
    ], options={"ordering": ("-created_at", "-id"), "indexes": [models.Index(fields=("status", "created_at"), name="inquiries_i_status_8d3c50_idx"), models.Index(fields=("user", "created_at"), name="inquiries_i_user_id_6a5c03_idx")]}),
    migrations.AddConstraint(model_name="inquiry", constraint=models.UniqueConstraint(condition=models.Q(status__in=("OPEN", "CONTACTED")), fields=("user", "plan"), name="inquiry_one_open_plan_per_user")),]
