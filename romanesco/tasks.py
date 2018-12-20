import os

from abc import ABCMeta, abstractmethod
import json

import shutil

from evaluation2.formatting import green, blue


def write_metadata_at_end(func):
    """ Decorator so that a class function can call the write_metadata class function
    after finishing"""
    def wrapper_func(self, *args, **kwargs):
        # Invoke the wrapped function first
        retval = func(self, *args, **kwargs)
        self.write_metadata()
        return retval
    return wrapper_func


class Task:
    __metaclass__ = ABCMeta

    def __init__(self, force=False, output_type="plain", prev_tasks=None, **kwargs):
    
        self._force = force
        self._output_type = output_type
        if prev_tasks is None:
            self._prev_tasks = []
        else:
            self._prev_tasks = prev_tasks
        self._settings = kwargs

    @abstractmethod
    def name(self):
        pass

    def checksum(self):
        csum = reduce(lambda x,y : x^y, [hash(item) for item in self.settings().items()])
        return str(abs(csum))

    def add_previous_task(self, task):
        # sets a direct dependency
        self._prev_tasks.append(task)

    def set_force(self, force):
        self._force = force

    def force(self):
        return self._force

    def prev_tasks(self):
        return self._prev_tasks

    def settings(self):
        """ Get all the settings that uniquely define the task """
        settings = self._settings 
        dependent_settings = self.get_dependent_settings()
        for k,v in settings.iteritems():
            if k in dependent_settings and dependent_settings[k]!=v:
                raise Exception("Inconsistent settings: Trying to set value for {} to {} (already = {})".format(k, v, dependent_settings[k]))
            dependent_settings[k] = v
        return dependent_settings 

    def update_settings(self, k, v):
        self._settings[k] = v

    def check_requirements(self):
        """ Override this to check requirements before running the pipeline """
        return

    @abstractmethod
    def is_already_complete(self):
        pass


    def get_dependent_settings(self):
        """ Gets the settings from dependent tasks to uniquely define the task"""
        res = {}
        for task in self.prev_tasks():
            for k,v in task.settings().iteritems():
                if k in res and res[k]!=v:
                    raise Exception("Inconsistent settings: Trying to set value for {} to {} (already = {})".format(k, v, res[k]))
                res[k] = v

        return res

    @abstractmethod
    def output(self):
        """ The output should be unique according to the settings """
        pass

    @abstractmethod
    def clean(self):
        pass

    @abstractmethod
    def _run(self):
        pass

    @write_metadata_at_end
    def run(self, force_defined_externally=False):
        if not self.force() and not force_defined_externally and self.is_already_complete():
            print "Task {} (settings : {}) : {} at {}".format(green(self.name()), self.settings(), blue("Already complete"), self.output())
            return self.output()
        elif self.force():
            print "Task {} (settings : {}) : {} because force is set to True. Will replace output {}".format(green(self.name()), self.settings(), green("Rerun"), self.output())
        else:
            print "{} (settings : {}) {} Expected output : {}".format(green(self.name()), self.settings(), green("Running"), self.output())
        self.check_requirements()
        self.clean()
        self._run()


class FileOutputTask(Task):
    """ Class that has a file as an output. So far those are the only tasks we are using. """
    
    METADATA_SUFFIX = ".meta"

    def get_metadata_file(self):
        return self.output() + self.METADATA_SUFFIX

    def write_metadata(self):
        with open(self.get_metadata_file(), 'w') as outf:
            json.dump(self.settings(), outf)

    def clean(self):
        out = self.output()
        if os.path.isdir(out):
            shutil.rmtree(out)
        elif os.path.exists(out):
            os.remove(out)

    def is_already_complete(self):
        output_exists = os.path.exists(self.output())
        if not output_exists:
            return False
        metadata_file = self.get_metadata_file()
        if not os.path.exists(metadata_file):
           # raise Exception("Task "+self.name()+" didn't write metadata. It's possible it's already existing output" +
           # " {} is incomplete. Either manually remove the output or specify force=True to clean and rerun everything".format(self.output()))
           self.clean()
           return False 
        with open(metadata_file, 'r') as inf:
            json_str = inf.read()
        try:
            settings_that_have_been_saved = json.loads(json_str)
        except Exception as e:
            raise Exception("Task {} didn't write metadata properly at {} (exception when reading json_str {} : {}). It's possible it's already existing output {} is incomplete. Either manually remove the output or specify force=True to clean and rerun everything".format(self.name(), metadata_file,
                json_str, e, self.output()))
        is_complete = settings_that_have_been_saved  == self.settings()
        if not is_complete:
            print "Saved settings {} do not match specified {} so task needs to rerun".format(settings_that_have_been_saved, self.settings())
        return is_complete

