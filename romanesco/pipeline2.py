from abc import ABCMeta, abstractmethod
from datetime import datetime
import json
import time

from celery import group

from evaluation2 import celeryapp, celery_utils

class SingleSessionPipeline(object):
    """A pipeline for which we assume no parallelization is possible,
    so the tasks will be done linearly. This is just an abstraction
    so that we don't have a lot of boilerplate when chaining tasks"""

    def __init__(self, **kwargs):
        # the default one is empty
        self.tasks = [] # Subclasses should add tasks to this list
        self._settings = kwargs
        self.last_output = None
        self.exec_stats = []

    def update_statistics(self, task_name, seconds_elapsed):
        self.exec_stats.append({"task_name":task_name, "seconds_elapsed":seconds_elapsed})

    def write_statistics(self, outfile):
        with open(outfile, 'w') as f:
            json.dump({"statistics":self.exec_stats, "output": self.output()}, f)


    def output(self):
        """Subclasses can override this to return something else rather than the very last task's output"""
        return self.last_output

    def settings(self):
        return self._settings

    def tasklist(self):
        return self.tasks

    def run(self, force=False):
        output = None
        for task in self.tasklist():
            task.run(force_defined_externally=force)
            output = task.output()
        self.last_output = output
        return output


@celeryapp.task
def run_pipeline_celery(pipeline, force=False):
    for task in pipeline.tasklist():
        # can't update the state outside of a function tagged @celery unfortunately
        run_pipeline_celery.update_state(state="Running task {}".format(task.name()), meta=str(task.settings()))
        start = datetime.now()
        task.run(force_defined_externally=force)
        end = datetime.now()
        pipeline.update_statistics(task.name(), (end-start).total_seconds())
    return pipeline.output(), pipeline


class MultiSessionPipeline(object):

    """A pipeline which runs some prep work, several single session pipelines in parallel,
    and does some aggregate
    work after. When parellelism is not available, it can also be run in serial mode.
    """

    __metaclass__ = ABCMeta

    def __init__(self, celery_parent_task=None, force=False):

        self.meta = celery_utils.generate_task_meta()
        self.force = force
        self.celery_parent_task = celery_parent_task


    def update_state(self, state):
        self.celery_parent_task.update_state(state=state, meta=self.meta)

    @abstractmethod
    def get_all_contained_single_session_pipelines(self):
        """ Get a list of all the SingleSessionPipeline instances
         that need to run in parallel
        """
        pass

    @abstractmethod
    def run_before_sessions(self, force=False):
        """ Do the preparatory work, for instance fetching repos etc
        before starting the session processing
        """
        pass

    @abstractmethod
    def run_after_sessions(self, session_results, force=False):
        """ Do the post processing work after processing all sessions, for instance
        making a report
        """
        pass

    def get_each_single_session_pipeline_as_celery_task(self):
        tasks = []
        for pipeline in self.get_all_contained_single_session_pipelines():
            session_pipeline_as_task = run_pipeline_celery.s(pipeline=pipeline, force=self.force)
            tasks.append(session_pipeline_as_task)
        return tasks


    def run(self):
        self.run_before_sessions()
        return self.run_sessions_parallel()

    def run_sessions_parallel(self):

        celery_tasks = self.get_each_single_session_pipeline_as_celery_task()
        group_async_res = group(celery_tasks).apply_async()
        for (is_done, children_states_summary) in celery_utils.get_status_for_group_of_tasks(group_async_res):
            self.update_state(children_states_summary)
            if is_done:
                return self.run_after_sessions(group_async_res.results)
            time.sleep(2)