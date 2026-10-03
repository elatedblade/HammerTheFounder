from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ai", "0001_initial")]

    operations = [
        migrations.AddField(model_name="airun", name="agent_version", field=models.CharField(max_length=80, default="legacy-unversioned")),
        migrations.AddField(model_name="airun", name="prompt_version", field=models.CharField(max_length=80, default="legacy-unversioned")),
        migrations.AddField(model_name="airun", name="source_references", field=models.JSONField(default=dict)),
        migrations.AlterField(model_name="airun", name="agent_version", field=models.CharField(max_length=80, default="htf-assistance-v2")),
        migrations.AlterField(model_name="airun", name="prompt_version", field=models.CharField(max_length=80, default="canonical-facts-v1")),
    ]
