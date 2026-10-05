from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("inquiries", "0001_initial")]
    operations = [
        migrations.RemoveConstraint(model_name="inquiry", name="inquiry_one_open_plan_per_user"),
        migrations.AddConstraint(model_name="inquiry", constraint=models.UniqueConstraint(condition=models.Q(status__in=("OPEN", "CONTACTED")), fields=("user", "plan"), name="inquiry_one_open_plan_per_user")),
    ]
