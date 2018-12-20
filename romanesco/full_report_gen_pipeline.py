import os
from tt_backend.utils import env, filenames

from evaluation2.pipeline2 import SingleSessionPipeline, MultiSessionPipeline
from evaluation2.nb_utils import overwrite_input_folders_and_generate
from evaluation2.common_pipelines import  create_sima_imu_fa_pipeline, create_repos_pipeline 
from evaluation2.copy_tasks import SymlinkGroundTruth

__author__ = 'carolinux'


class FetchRepos(SingleSessionPipeline):
    """ Fetch the necessary repos to do the full end to end pipeline """


    def __init__(self, base_dir="/tmp/", fa_hash=None, gtsam_hash=None, **kwargs):
        super(FetchRepos, self).__init__(**kwargs)
        self.repo_tasks = create_repos_pipeline(base_dir=base_dir, fa_hash=fa_hash, gtsam_hash=gtsam_hash)
        self.tasks = [self.repo_tasks["imu"], self.repo_tasks["fa"], self.repo_tasks["gtsam"]]

    def get_repo_tasks(self):
        return self.repo_tasks



class EndToEndFa(SingleSessionPipeline):
    """ Run the everything from raw bin to fusion algorithm."""


    def __init__(self, raw_binary="", directory_with_ground_truth="", tracker_id="",
            repo_tasks=None, base_dir="/tmp/", calibration_dt=None,
            **kwargs):
        super(EndToEndFa, self).__init__(**kwargs)
        have_matlab_license = env.get_true_false_env_value("HAVE_MATLAB_LICENSE", optional=False)
        sima, imu, imu_cal, fa = create_sima_imu_fa_pipeline(base_dir, tracker_id, input_bin=raw_binary,
                repo_tasks=repo_tasks, calibration_dt=calibration_dt, have_matlab_license=have_matlab_license)
        ground_truth_copy = SymlinkGroundTruth(in_dir=directory_with_ground_truth, out_dir=fa.output(), force=True)
        self.tasks = [sima, imu_cal, imu, fa, ground_truth_copy]

    def output(self):
        """
        Returns the output of the FA task
        If it wasn't overriden it would return the output of the ground truth copy which 
        is not what we want, semantically
        """
        return self.tasks[-2].output()

class ReportGenerationPipeline(MultiSessionPipeline):

    def __init__(self, input_data, fa_hash="latest", gtsam_hash="latest",
                 base_dir="/tmp/", calibration_dt=None, output_file=None, notebook=None,
                 **kwargs):
        """Input data is a list of tuples (raw_binary, ground_truth_directory, tracker_id)
        for instance:
        data = [("/media/disk2/evaldata/05_new_rtk_gt2/session_UBPup-01UX7BloPS/session_UBPup-01UX7BloPS.bin",
        "/media/disk2/evaldata/05_new_rtk_gt2/session_UBPup-01UX7BloPS/", "UBPup")]

        Those are given explicitly so that the task doesn't need to know about file system storage or naming conventions
        """

        super(ReportGenerationPipeline, self).__init__(**kwargs)
        self.notebook = notebook
        self.output_file = output_file

        self.update_state("Initializing task - determining calibration dates")
        self.pipelines = []
        self.fetch_repos = FetchRepos(base_dir=base_dir, fa_hash=fa_hash, gtsam_hash=gtsam_hash)
        for raw_bin, grt_dir, tracker_id in input_data:
            pipeline =  EndToEndFa(raw_binary=raw_bin,
                    directory_with_ground_truth=grt_dir, tracker_id=tracker_id,
                    base_dir=base_dir, repo_tasks=self.fetch_repos.get_repo_tasks(),
                    calibration_dt=calibration_dt)
            self.pipelines.append(pipeline)


    def get_all_contained_single_session_pipelines(self):
        return self.pipelines

    def run_before_sessions(self):
        self.update_state("Running prerequisites: Fetching repos")
        self.fetch_repos.run(force=self.force)


    def run_after_sessions(self, session_results):
        """
         Generate the report
        """
        self.update_state("Creating report")
        fa_folders = [r.result[0] for r in session_results]
        pipelines = [r.result[1] for r in session_results]
        # write out statistics
        # For now writing just the statistics of the first two sessions
        stat_files = []
        for pipeline, fa_folder in zip(pipelines, fa_folders)[:2]:
            outfile = os.path.join(fa_folder, filenames.EV2_TIME_STATS_FN)
            pipeline.write_statistics(outfile)
            stat_files.append(outfile)
        # generate notebook
        try:
            overwrite_input_folders_and_generate(self.notebook, self.output_file, replace_dict={"input_folders":fa_folders},
                                                 statistics_files=stat_files)
        except Exception as e:
            raise Exception("Generating notebook {} failed.<br>{}".format(self.notebook, e))
        return self.output_file



class ReportGenerationPipelineCommmitDiff(MultiSessionPipeline):

    def __init__(self, input_data, fa_hash1="latest", fa_hash2="latest", gtsam_hash="latest",
                 base_dir="/tmp/", calibration_dt=None, output_file=None, notebook=None,
                 **kwargs):
        """Input data is a list of tuples (raw_binary, ground_truth_directory, tracker_id)
        for instance:
        data = [("/media/disk2/evaldata/05_new_rtk_gt2/session_UBPup-01UX7BloPS/session_UBPup-01UX7BloPS.bin",
        "/media/disk2/evaldata/05_new_rtk_gt2/session_UBPup-01UX7BloPS/", "UBPup")]

        Those are given explicitly so that the task doesn't need to know about file system storage or naming conventions
        """

        super(ReportGenerationPipelineCommmitDiff, self).__init__(**kwargs)
        self.notebook = notebook
        self.output_file = output_file

        self.update_state("Initializing task - determining calibration dates")
        self.pipelines = []
        self.fa_hash1 = fa_hash1
        self.fa_hash2 = fa_hash2
        self.fetch_repos1 = FetchRepos(base_dir=base_dir, fa_hash=fa_hash1, gtsam_hash=gtsam_hash)
        self.fetch_repos2 = FetchRepos(base_dir=base_dir, fa_hash=fa_hash2, gtsam_hash=gtsam_hash)
        for repos in [self.fetch_repos1, self.fetch_repos2]:
            for raw_bin, grt_dir, tracker_id in input_data:
                pipeline =  EndToEndFa(raw_binary=raw_bin,
                    directory_with_ground_truth=grt_dir, tracker_id=tracker_id,
                    base_dir=base_dir, repo_tasks=repos.get_repo_tasks(),
                    calibration_dt=calibration_dt)
            self.pipelines.append(pipeline)

    def get_all_contained_single_session_pipelines(self):
        return self.pipelines

    def run_before_sessions(self):
        self.update_state("Running prerequisites: Fetching repos - first commit hash {}".format(self.fa_hash1))
        self.fetch_repos1.run(force=self.force)
        self.update_state("Running prerequisites: Fetching repos - second commit hash {}".format(self.fa_hash2))
        self.fetch_repos2.run(force=self.force)


    def run_after_sessions(self, session_results):
        """
         Generate the report
        """
        self.update_state("Creating report")
        # generate notebook
        middle_idx = len(session_results)/2
        fa_folders1 = [r.result[0] for r in session_results[:middle_idx]]
        fa_folders2 = [r.result[0] for r in session_results[middle_idx:]]

        try:
            overwrite_input_folders_and_generate(self.notebook, self.output_file, replace_dict={
                "input_folders1":fa_folders1, "input_folders2": fa_folders2, "input_folders":[
                fa_folders1[0], fa_folders2[0]]})
        except Exception as e:
            import traceback
            raise Exception("Generating notebook {} failed.<br>{} {}".format(self.notebook, e, traceback.format_exc()))
        return self.output_file




