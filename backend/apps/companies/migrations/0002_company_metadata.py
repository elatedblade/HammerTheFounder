from django.db import migrations, models


def backfill_company_fields(apps, schema_editor):
    Company = apps.get_model("companies", "Company")
    for company in Company.objects.all().iterator():
        normalized = " ".join(company.name.split()).casefold()
        company.normalized_name = normalized
        company.identity_key = f"name:{normalized}"
        company.save(update_fields=("normalized_name", "identity_key"))


class Migration(migrations.Migration):
    dependencies = [("companies", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="company",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="company",
            name="metadata_json",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="company",
            name="normalized_name",
            field=models.CharField(editable=False, max_length=200, null=True),
        ),
        migrations.RunPython(backfill_company_fields, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="company",
            name="normalized_name",
            field=models.CharField(editable=False, max_length=200, unique=True),
        ),
    ]
