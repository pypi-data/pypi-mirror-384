import logging
from datetime import timedelta

from core.choices import DataSourceStatusChoices
from core.choices import JobStatusChoices
from core.exceptions import SyncError
from netbox.context_managers import event_tracking
from rq.timeouts import JobTimeoutException
from utilities.datetime import local_now
from utilities.request import NetBoxFakeRequest

from .models import IPFabricIngestion
from .models import IPFabricSource
from .models import IPFabricSync

logger = logging.getLogger(__name__)


def sync_ipfabricsource(job, *args, **kwargs):
    ipfsource = IPFabricSource.objects.get(pk=job.object_id)

    try:
        job.start()
        ipfsource.sync(job=job)
        job.terminate()
    except Exception as e:
        job.terminate(status=JobStatusChoices.STATUS_ERRORED)
        IPFabricSource.objects.filter(pk=ipfsource.pk).update(
            status=DataSourceStatusChoices.FAILED
        )
        if type(e) in (SyncError, JobTimeoutException):
            logging.error(e)
        else:
            raise e


def sync_ipfabric(job, *args, **kwargs):
    sync = IPFabricSync.objects.get(pk=job.object_id)

    try:
        job.start()
        sync.sync(job=job)
        job.terminate()
    except Exception as e:
        job.terminate(status=JobStatusChoices.STATUS_ERRORED)
        IPFabricSync.objects.filter(pk=sync.pk).update(
            status=DataSourceStatusChoices.FAILED
        )
        if type(e) in (SyncError, JobTimeoutException):
            logging.error(e)
        else:
            raise e
    finally:
        if sync.interval and not kwargs.get("adhoc"):
            new_scheduled_time = local_now() + timedelta(minutes=sync.interval)
            # We want to create new Job only if scheduled time was before this Job started
            # The current sync might have been changed while this job was running
            sync.refresh_from_db()
            if not sync.scheduled or (
                sync.scheduled
                and sync.scheduled > job.started
                and sync.jobs.filter(
                    status__in=[
                        JobStatusChoices.STATUS_SCHEDULED,
                        JobStatusChoices.STATUS_PENDING,
                        JobStatusChoices.STATUS_RUNNING,
                    ]
                )
                .exclude(pk=job.pk)
                .exists()
            ):
                logger.info(
                    f"Not scheduling a new job for IPFabricSync {sync.pk} as the scheduled time was changed while the job was running."
                )
                return
            # Update the sync object with the new scheduled time
            # This also triggers the creation of a new Job
            # Running in fake request context to ensure user is set for changelog
            request = NetBoxFakeRequest(
                {
                    "META": {},
                    "POST": sync.parameters,
                    "GET": {},
                    "FILES": {},
                    "user": sync.user,
                    "path": "",
                    "id": job.job_id,
                }
            )

            with event_tracking(request):
                sync.scheduled = new_scheduled_time
                sync.status = DataSourceStatusChoices.QUEUED
                sync.full_clean()
                sync.save()
            logger.info(
                f"Scheduled next sync for IPFabricSync {sync.pk} at {new_scheduled_time}."
            )


def merge_ipfabric_ingestion(job, remove_branch=False, *args, **kwargs):
    ingestion = IPFabricIngestion.objects.get(pk=job.object_id)
    try:
        request = NetBoxFakeRequest(
            {
                "META": {},
                "POST": ingestion.sync.parameters,
                "GET": {},
                "FILES": {},
                "user": ingestion.sync.user,
                "path": "",
                "id": job.job_id,
            }
        )

        job.start()
        with event_tracking(request):
            ingestion.sync_merge()
        if remove_branch:
            branching_branch = ingestion.branch
            ingestion.branch = None
            ingestion.save()
            branching_branch.delete()
        job.terminate()
    except Exception as e:
        print(e)
        job.terminate(status=JobStatusChoices.STATUS_ERRORED)
        IPFabricSync.objects.filter(pk=ingestion.sync.pk).update(
            status=DataSourceStatusChoices.FAILED
        )
        if type(e) in (SyncError, JobTimeoutException):
            logging.error(e)
        else:
            raise e
