from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("inquiries", "0002_contacted_retry_constraint")]
    operations = [migrations.AlterField(model_name="inquiry", name="reference", field=models.CharField(editable=False, max_length=40, unique=True))]
