import os
import shutil

from tt_api import data as tt_data, commits
from tt_backend.utils import Fn, pipeline, Files

from tasks import FileOutputTask



COMPILES_PREVIOUS_VERSION = "Compiles previous version"

class CheckoutTTRepoFromWeb(FileOutputTask):

    def __init__(self, repo="", commit_hash="latest", base_dir="/tmp", **kwargs):

        # no need to pass base dir into the task constructor
        super(CheckoutTTRepoFromWeb, self).__init__(**kwargs)

        self.repo = repo
        if commit_hash == "latest":
            commit_hash = commits.get_latest_commit_hash(repo=self.repo)
        elif commit_hash == "latest_compiled": # only for MATLAB
            commit_hash = commits.get_latest_commit_hash(repo=self.repo, title=COMPILES_PREVIOUS_VERSION)
        self.commit_hash = commit_hash
        self.base_dir = base_dir
        self.base_repo_dir = os.path.join(base_dir, "{}_{}".format(self.repo, self.commit_hash))

        self.update_settings(repo+"_commit_hash", commit_hash)

    def cleanup(self):
        shutil.rmtree(self.base_repo_dir)
        
    def name(self):
        return "CheckoutTTRepoFromWeb"

    def _run(self):
        url = "git@bitbucket.org:tracktics/{}.git".format(self.repo)
        Files.make_dir_if_not_exists(self.base_repo_dir)
        pipeline.checkout_code_from_url(url, self.commit_hash, self.base_repo_dir) 

    def output(self):
        return os.path.join(self.base_repo_dir, self.repo) # checkout code from url creates the repo on that folder


        
