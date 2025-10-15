from datetime import timedelta
from typing import TYPE_CHECKING

from django.db import migrations
from utilities.datetime import local_now

if TYPE_CHECKING:
    from django.apps import apps as apps_type
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def clean_scheduled_jobs(
    apps: "apps_type", schema_editor: "BaseDatabaseSchemaEditor"
) -> None:
    Job = apps.get_model("core", "Job")
    IPFabricSync = apps.get_model("ipfabric_netbox", "IPFabricSync")
    ObjectType = apps.get_model("core", "ObjectType")

    for sync in IPFabricSync.objects.all():
        try:
            scheduled_jobs = Job.objects.filter(
                object_id=sync.id,
                object_type=ObjectType.objects.get_for_model(sync),
                scheduled__isnull=False,
            ).order_by("scheduled")
            if not scheduled_jobs.exists():
                continue
            if not sync.scheduled:
                # Delete all scheduled jobs if the sync is not scheduled
                scheduled_jobs.delete()
                continue
            if scheduled_jobs.count() == 1:
                # Only one scheduled job exists, let's update scheduled time on the sync object
                # This does not create a new job since sync is a Faked object in migration
                sync.scheduled = scheduled_jobs.first().scheduled
                sync.full_clean()
                sync.save()
                continue
            # More than one scheduled job exists
            # Find the one that is closest to scheduled + N * interval
            interval = timedelta(minutes=sync.interval)
            elapsed = local_now() - sync.scheduled
            intervals_passed = (elapsed // interval) + 1
            closest_future_scheduled = sync.scheduled + intervals_passed * interval
            closest_job = min(
                scheduled_jobs,
                key=lambda job: abs(job.scheduled - closest_future_scheduled),
            )
            for job in scheduled_jobs:
                if job != closest_job:
                    job.delete()
            sync.scheduled = closest_job.scheduled
            sync.full_clean()
            sync.save()
        except Exception as err:
            # Always be safe inside a migration
            print(f"Error cleaning scheduled jobs for IPFabricSync {sync.id}: {err}")


class Migration(migrations.Migration):
    dependencies = [
        (
            "ipfabric_netbox",
            "0019_alter_ipfabrictransformmap_options_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(clean_scheduled_jobs, migrations.RunPython.noop),
    ]
