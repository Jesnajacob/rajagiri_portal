from django.db import migrations


def remove_legacy_announcements(apps, schema_editor):
    Announcement = apps.get_model("core", "Announcement")
    Announcement.objects.filter(category__in={"rlabs", "research", "events"}).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]
    operations = [migrations.RunPython(remove_legacy_announcements, migrations.RunPython.noop)]