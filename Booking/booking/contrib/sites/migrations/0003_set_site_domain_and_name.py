from django.db import migrations

def update_site_forward(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    db_alias = schema_editor.connection.alias
    Site.objects.using(db_alias).update_or_create(
        id=1,
        defaults={"domain": "localhost:8000", "name": "localhost"},
    )

def update_site_reverse(apps, schema_editor):
    pass  # Pas de rollback nécessaire

class Migration(migrations.Migration):
    dependencies = [
        ("sites", "0002_alter_domain_unique"),
    ]
    operations = [
        migrations.RunPython(
            update_site_forward, update_site_reverse
        ),
    ]
