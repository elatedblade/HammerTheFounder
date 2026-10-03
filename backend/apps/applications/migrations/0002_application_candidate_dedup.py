from django.db import migrations, models
import django.db.models.deletion


def populate_candidates(apps, schema_editor):
    Application = apps.get_model("applications", "Application")
    for row in Application.objects.using(schema_editor.connection.alias).select_related("campaign").iterator():
        Application.objects.using(schema_editor.connection.alias).filter(pk=row.pk).update(candidate_id=row.campaign.candidate_id)


class Migration(migrations.Migration):
    dependencies = [("applications", "0001_initial"), ("candidates", "0002_candidateprofile_expected_ctc_max_and_more")]
    operations = [
        migrations.AddField(model_name="application", name="candidate", field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="applications", to="candidates.candidateprofile")),
        migrations.RunPython(populate_candidates, migrations.RunPython.noop),
        migrations.AlterField(model_name="application", name="candidate", field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name="applications", to="candidates.candidateprofile")),
        migrations.AddConstraint(model_name="application", constraint=models.UniqueConstraint(fields=("candidate", "job"), name="application_candidate_job_unique")),
    ]
