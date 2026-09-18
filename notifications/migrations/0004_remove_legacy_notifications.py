from django.db import migrations


def remove_legacy_notifications(apps, schema_editor):
    Notification = apps.get_model("notifications", "Notification")
    Notification.objects.filter(category__in={"rlabs", "research", "events"}).delete()


class Migration(migrations.Migration):
    dependencies = [("notifications", "0003_remove_notificationpreference_event_emails_and_more")]
    operations = [migrations.RunPython(remove_legacy_notifications, migrations.RunPython.noop)]