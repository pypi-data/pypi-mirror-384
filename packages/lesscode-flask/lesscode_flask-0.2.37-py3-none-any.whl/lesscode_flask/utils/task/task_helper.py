import importlib

from flask import request
from requests import post

from lesscode_flask.app import current_app


class TaskHelper:
    @staticmethod
    def add_job(func, trigger=None, args=None, kwargs=None, id=None, name=None,
                misfire_grace_time=None, coalesce=None, max_instances=None,
                next_run_time=None, jobstore='default', executor='default',
                replace_existing=False, is_add_ctx=False, **trigger_args):
        try:
            util = importlib.import_module("apscheduler.util")
        except ImportError:
            raise Exception(f"flask_apscheduler is not exist,run:pip install flask_apscheduler==1.13.1")
        if misfire_grace_time is None:
            misfire_grace_time = util.undefined
        if coalesce is None:
            coalesce = util.undefined
        if max_instances is None:
            max_instances = util.undefined
        if next_run_time is None:
            next_run_time = util.undefined
        scheduler = getattr(current_app, 'apscheduler')
        if is_add_ctx:
            _func = post
            _kwargs = {
                "url": f"http://127.0.0.1:{current_app.config.get('PORT')}{current_app.config.get('ROUTE_PREFIX')}/task_run",
                "json": {"func_key": f"{func.__module__}:{func.__qualname__}",
                         "task_params": kwargs, },
                "headers": dict(request.headers)}
            job = scheduler.add_job(func=_func, trigger=trigger, args=args, kwargs=_kwargs, id=id, name=name,
                                    misfire_grace_time=misfire_grace_time, coalesce=coalesce,
                                    max_instances=max_instances,
                                    next_run_time=next_run_time, jobstore=jobstore, executor=executor,
                                    replace_existing=replace_existing, **trigger_args)
        else:
            job = scheduler.add_job(func=func, trigger=trigger, args=args, kwargs=kwargs, id=id, name=name,
                                    misfire_grace_time=misfire_grace_time, coalesce=coalesce,
                                    max_instances=max_instances,
                                    next_run_time=next_run_time, jobstore=jobstore, executor=executor,
                                    replace_existing=replace_existing, **trigger_args)
        return job

    @staticmethod
    def scheduled_job(trigger, args=None, kwargs=None, id=None, name=None,
                      misfire_grace_time=None, coalesce=None, max_instances=None,
                      next_run_time=None, jobstore='default', executor='default',
                      **trigger_args):
        try:
            util = importlib.import_module("apscheduler.util")
        except ImportError:
            raise Exception(f"flask_apscheduler is not exist,run:pip install flask_apscheduler==1.13.1")
        if misfire_grace_time is None:
            misfire_grace_time = util.undefined
        if coalesce is None:
            coalesce = util.undefined
        if max_instances is None:
            max_instances = util.undefined
        if next_run_time is None:
            next_run_time = util.undefined
        scheduler = getattr(current_app, 'apscheduler')
        inner = scheduler.scheduled_job(trigger, args=args, kwargs=kwargs, id=id, name=name,
                                        misfire_grace_time=misfire_grace_time, coalesce=coalesce,
                                        max_instances=max_instances,
                                        next_run_time=next_run_time, jobstore=jobstore, executor=executor,
                                        **trigger_args)
        return inner

    @staticmethod
    def modify_job(job_id, jobstore=None, **changes):
        scheduler = getattr(current_app, 'apscheduler')
        job = scheduler.modify_job(job_id, jobstore=jobstore, **changes)
        return job

    @staticmethod
    def reschedule_job(job_id, jobstore=None, trigger=None, **trigger_args):
        scheduler = getattr(current_app, 'apscheduler')
        job = scheduler.reschedule_job(job_id, jobstore=jobstore, trigger=trigger, **trigger_args)
        return job

    @staticmethod
    def pause_job(job_id, jobstore=None):
        scheduler = getattr(current_app, 'apscheduler')
        job = scheduler.pause_job(job_id, jobstore=jobstore)
        return job

    @staticmethod
    def resume_job(job_id, jobstore=None):
        scheduler = getattr(current_app, 'apscheduler')
        job = scheduler.resume_job(job_id, jobstore=jobstore)
        return job

    @staticmethod
    def get_jobs(jobstore=None, pending=None):
        scheduler = getattr(current_app, 'apscheduler')
        jobs = scheduler.get_jobs(jobstore=jobstore, pending=pending)
        return jobs

    @staticmethod
    def get_job(job_id, jobstore=None):
        scheduler = getattr(current_app, 'apscheduler')
        job = scheduler.get_job(job_id, jobstore=jobstore)
        return job

    @staticmethod
    def remove_job(job_id, jobstore=None):
        scheduler = getattr(current_app, 'apscheduler')
        scheduler.remove_job(job_id, jobstore=jobstore)

    @staticmethod
    def remove_all_jobs(jobstore=None):
        scheduler = getattr(current_app, 'apscheduler')
        scheduler.remove_all_jobs(jobstore=jobstore)

    @staticmethod
    def print_jobs(jobstore=None, out=None):
        scheduler = getattr(current_app, 'apscheduler')
        scheduler.print_jobs(jobstore=jobstore, out=out)

    @staticmethod
    def add_executor(executor, alias='default', **executor_opts):
        scheduler = getattr(current_app, 'apscheduler')
        scheduler.add_executor(executor, alias=alias, **executor_opts)

    @staticmethod
    def remove_executor(alias, shutdown=True):
        scheduler = getattr(current_app, 'apscheduler')
        scheduler.remove_executor(alias=alias, shutdown=shutdown)

    @staticmethod
    def add_jobstore(jobstore, alias='default', **jobstore_opts):
        scheduler = getattr(current_app, 'apscheduler')
        scheduler.add_jobstore(jobstore, alias=alias, **jobstore_opts)

    @staticmethod
    def remove_jobstore(alias, shutdown=True):
        scheduler = getattr(current_app, 'apscheduler')
        scheduler.remove_jobstore(alias=alias, shutdown=shutdown)

    @staticmethod
    def add_listener(callback, mask=None):
        try:
            events = importlib.import_module("apscheduler.events")
        except ImportError as e:
            raise Exception(f"flask_apscheduler is not exist,run:pip install flask_apscheduler==1.13.1")
        if mask is None:
            mask = events.EVENT_ALL
        scheduler = getattr(current_app, 'apscheduler')
        scheduler.add_listener(callback, mask=mask)

    @staticmethod
    def remove_listener(callback):
        scheduler = getattr(current_app, 'apscheduler')
        scheduler.remove_listener(callback)
