from django.conf import settings

import auditor

from event_manager.events.job import JOB_LOGS_VIEWED
from streams.authentication import authorized
from streams.resources.logs import log_job
from streams.resources.utils import get_error_message
from streams.validation.job import validate_job


@authorized()
async def job_logs_v2(request, ws, username, project_name, job_id):
    job, message = validate_job(request=request,
                                username=username,
                                project_name=project_name,
                                job_id=job_id)
    if job is None:
        await ws.send(get_error_message(message))
        return

    pod_id = job.pod_id

    auditor.record(event_type=JOB_LOGS_VIEWED,
                   instance=job,
                   actor_id=request.app.user.id,
                   actor_name=request.app.user.username)

    # Stream logs
    await log_job(request=request,
                  ws=ws,
                  job=job,
                  pod_id=pod_id,
                  container=settings.CONTAINER_NAME_JOB,
                  namespace=settings.K8S_NAMESPACE)
