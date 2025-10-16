# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-01-09
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Schedule methods.
"""


from typing import Any, Literal, TypedDict, NotRequired
from functools import wraps as functools_wraps
from collections.abc import Callable
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.job import Job
from reydb import rorm, DatabaseEngine

from .rbase import Base, throw


__all__ = (
    'DatabaseORMTableSchedule',
    'Schedule'
)


class DatabaseORMTableSchedule(rorm.Table):
    """
    Database `schedule` table ORM model.
    """

    __name__ = 'schedule'
    __comment__ = 'Schedule execute record table.'
    create_time: rorm.Datetime = rorm.Field(field_default=':create_time', not_null=True, index_n=True, comment='Record create time.')
    update_time: rorm.Datetime = rorm.Field(field_default=':update_time', index_n=True, comment='Record update time.')
    id: int = rorm.Field(rorm.types_mysql.INTEGER(unsigned=True), key_auto=True, comment='ID.')
    status: str = rorm.Field(rorm.types_mysql.TINYINT(unsigned=True), not_null=True, comment='Schedule status, 0 is executing, 1 is completed, 2 is occurred error.')
    task: str = rorm.Field(rorm.types.VARCHAR(100), not_null=True, comment='Schedule task function name.')
    note: str = rorm.Field(rorm.types.VARCHAR(500), comment='Schedule note.')


class Schedule(Base):
    """
    Schedule type.
    Can create database used `self.build_db` method.
    """


    def __init__(
        self,
        max_workers: int = 10,
        max_instances: int = 1,
        coalesce: bool = True,
        block: bool = False,
        db_engine: DatabaseEngine | None = None
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        max_workers : Maximum number of synchronized executions.
        max_instances : Maximum number of synchronized executions of tasks with the same ID.
        coalesce : Whether to coalesce tasks with the same ID.
        block : Whether to block.
        db_engine : Database engine.
            - `None`: Not use database.
            - `Database`: Automatic record to database.
        """

        # Build.

        ## Scheduler.
        executor = ThreadPoolExecutor(max_workers)
        executors = {'default': executor}
        job_defaults = {
            'coalesce': coalesce,
            'max_instances': max_instances
        }
        if block:
            scheduler = BlockingScheduler(
                executors=executors,
                job_defaults=job_defaults
            )
        else:
            scheduler = BackgroundScheduler(
                executors=executors,
                job_defaults=job_defaults
            )
        self.scheduler = scheduler

        ### Start.
        self.scheduler.start()

        ## Database.
        self.db_engine = db_engine

        ### Build Database.
        if self.db_engine is not None:
            self.build_db()


    def build_db(self) -> None:
        """
        Check and build database tables.
        """

        # Check.
        if self.db_engine is None:
            throw(ValueError, self.db_engine)

        # Parameter.
        database = self.db_engine.database

        ## Table.
        tables = [DatabaseORMTableSchedule]

        ## View stats.
        views_stats = [
            {
                'path': 'stats_schedule',
                'items': [
                    {
                        'name': 'count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{database}`.`schedule`'
                        ),
                        'comment': 'Schedule count.'
                    },
                    {
                        'name': 'past_day_count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{database}`.`schedule`\n'
                            'WHERE TIMESTAMPDIFF(DAY, `create_time`, NOW()) = 0'
                        ),
                        'comment': 'Schedule count in the past day.'
                    },
                    {
                        'name': 'past_week_count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{database}`.`schedule`\n'
                            'WHERE TIMESTAMPDIFF(DAY, `create_time`, NOW()) <= 6'
                        ),
                        'comment': 'Schedule count in the past week.'
                    },
                    {
                        'name': 'past_month_count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{database}`.`schedule`\n'
                            'WHERE TIMESTAMPDIFF(DAY, `create_time`, NOW()) <= 29'
                        ),
                        'comment': 'Schedule count in the past month.'
                    },
                    {
                        'name': 'task_count',
                        'select': (
                            'SELECT COUNT(DISTINCT `task`)\n'
                            f'FROM `{database}`.`schedule`'
                        ),
                        'comment': 'Task count.'
                    },
                    {
                        'name': 'last_time',
                        'select': (
                            'SELECT IFNULL(MAX(`update_time`), MAX(`create_time`))\n'
                            f'FROM `{database}`.`schedule`'
                        ),
                        'comment': 'Schedule last record time.'
                    }
                ]
            }
        ]

        # Build.
        self.db_engine.build.build(tables=tables, views_stats=views_stats, skip=True)

        # ## Error.
        self.db_engine.error.build_db()


    def pause(self) -> None:
        """
        Pause scheduler.
        """

        # Pause.
        self.scheduler.pause()


    def resume(self) -> None:
        """
        Resume scheduler.
        """

        # Resume.
        self.scheduler.resume()


    def tasks(self) -> list[Job]:
        """
        Return to task list.

        Returns
        -------
        Task list.
        """

        # Get.
        jobs = self.scheduler.get_jobs()

        return jobs


    __iter__ = tasks


    def wrap_record_db(
        self,
        task: Callable,
        note: str | None
    ) -> None:
        """
        Decorator, record to database.

        Parameters
        ----------
        task : Task.
        note : Task note.
        """


        @functools_wraps(task)
        def _task(*args, **kwargs) -> None:
            """
            Decorated function.

            Parameters
            ----------
            args : Position arguments of function.
            kwargs : Keyword arguments of function.
            """

            # Parameter.
            nonlocal task, note

            # Status executing.
            data = {
                'status': 0,
                'task': task.__name__,
                'note': note
            }
            with self.db_engine.connect() as conn:
                conn = self.db_engine.connect()
                conn.execute.insert(
                    'schedule',
                    data
                )
                id_ = conn.insert_id()

            # Try execute.

            ## Record error.
            task = self.db_engine.error.wrap(task, note=note)

            try:
                task(*args, **kwargs)

            # Status occurred error.
            except BaseException:
                data = {
                    'id': id_,
                    'status': 2
                }
                self.db_engine.execute.update(
                    'schedule',
                    data
                )
                raise

            # Status completed.
            else:
                data = {
                    'id': id_,
                    'status': 1
                }
                self.db_engine.execute.update(
                    'schedule',
                    data
                )

        return _task


    def add_task(
        self,
        task: Callable,
        plan: dict[str, Any],
        args: Any | None = None,
        kwargs: Any | None = None,
        note: str | None = None
    ) -> Job:
        """
        Add task.

        Parameters
        ----------
        task : Task function.
        plan : Plan trigger keyword arguments.
        args : Task position arguments.
        kwargs : Task keyword arguments.
        note : Task note.

        Returns
        -------
        Task instance.
        """

        # Parameter.
        if plan is None:
            plan = {}
        trigger = plan.get('trigger')
        trigger_args = {
            key: value
            for key, value in plan.items()
            if key != 'trigger'
        }

        # Add.

        ## Database.
        if self.db_engine is not None:
            task = self.wrap_record_db(task, note)

        job = self.scheduler.add_job(
            task,
            trigger,
            args,
            kwargs,
            **trigger_args
        )

        return job


    def modify_task(
        self,
        task: Job | str,
        plan: dict[str, Any],
        args: Any | None = None,
        kwargs: Any | None = None,
        note: str | None = None
    ) -> None:
        """
        Modify task.

        Parameters
        ----------
        task : Task instance or ID.
        plan : Plan trigger keyword arguments.
        args : Task position arguments.
        kwargs : Task keyword arguments.
        note : Task note.
        """

        # Parameter.
        if type(task) == Job:
            task = task.id
        if plan is None:
            plan = {}
        trigger = plan.get('trigger')
        trigger_args = {
            key: value
            for key, value in plan.items()
            if key != 'trigger'
        }

        # Modify plan.
        if plan != {}:
            self.scheduler.reschedule_job(
                task,
                trigger=trigger,
                **trigger_args
            )

        # Modify arguments.
        if (
            args != ()
            or kwargs != {}
        ):
            self.scheduler.modify_job(
                task,
                args=args,
                kwargs=kwargs
            )

        # Modify note.
        self.notes[task] = note


    def remove_task(
        self,
        task: Job | str
    ) -> None:
        """
        Remove task.

        Parameters
        ----------
        task : Task instance or ID.
        """

        # Parameter.
        if type(task) == Job:
            id_ = task.id
        else:
            id_ = task

        # Remove.
        self.scheduler.remove_job(id_)


    def pause_task(
        self,
        task: Job | str   
    ) -> None:
        """
        Pause task.

        Parameters
        ----------
        task : Task instance or ID.
        """

        # Parameter.
        if type(task) == Job:
            id_ = task.id
        else:
            id_ = task

        # Pause.
        self.scheduler.pause_job(id_)


    def resume_task(
        self,
        task: Job | str
    ) -> None:
        """
        Resume task.

        Parameters
        ----------
        task : Task instance or ID.
        """

        # Parameter.
        if type(task) == Job:
            id_ = task.id
        else:
            id_ = task

        # Resume.
        self.scheduler.resume_job(id_)
