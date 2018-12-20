"""
Tools to build commonly used pipelines
"""
import os

from tt_backend.utils import Fn

from evaluation2.download_tasks import DownloadCalibrationValues
from evaluation2.sima_task import SimaConvertBin
from evaluation2.matlab_tasks import ImuPreprocess, FuseKnowtion
from evaluation2.github_tasks import CheckoutTTRepoFromWeb


def create_sima_imu_fa_pipeline(base_dir, tracker_id, input_bin=None, prev_task=None,
        repo_tasks=None, have_matlab_license=False, calibration_dt=None):
    """ Create the tasks needed for a sima-imu-fa pipeline
    Args:
        base_dir: the base directory where the results are stored
        tracker id: tracker id for the session
        input_bin: path to the input binary
        previous_task: Optional, if a task was required to get the binary
    """

    _,uid,_ = Fn.fileparts(input_bin)
    task2 = SimaConvertBin(output_dir=os.path.join(base_dir, uid))
    task2.set_input_file(input_bin)
    if prev_task:
        task2.add_previous_task(prev_task)
    code_base_dir = base_dir
    task3b = DownloadCalibrationValues(tracker_id=tracker_id, base_dir=base_dir, use_calibration_before=calibration_dt)
    imu_pp_expected = repo_tasks["imu"].output()
    calib_json_expected = task3b.output()
    # imu preprocessor
    task3 = ImuPreprocess(imu_pp_code_directory=imu_pp_expected,
                          calibration_json=calib_json_expected,
                          matlab_installed=have_matlab_license, sima_dir=task2.output())
    task3.add_previous_task(task2)
    task3.add_previous_task(repo_tasks["imu"])
    task3.add_previous_task(task3b) # so that imu preprocess depends on calibration, imu pp hash and sima directory
    # fa
    fa_knowtion_expected = repo_tasks["fa"].output()
    task4 = FuseKnowtion(fa_knowtion_code_directory=fa_knowtion_expected, gtsam_dir=repo_tasks["gtsam"].output(), 
                         matlab_installed=have_matlab_license, sima_dir=task3.output())
    task4.add_previous_task(repo_tasks["fa"])
    task4.add_previous_task(repo_tasks["gtsam"])
    task4.add_previous_task(task3)
    return task2, task3, task3b, task4

def create_repos_pipeline(base_dir, fa_hash="latest", gtsam_hash="latest"):
    """ Create the tasks needed for a sima-imu-fa pipeline
    Args:
        base_dir: the base directory where the results are stored
        tracker id: tracker id for the session
        input_bin: path to the input binary
        previous_task: Optional, if a task was required to get the binary
    """

    code_base_dir = base_dir
    task3a = CheckoutTTRepoFromWeb(repo="tt-pl-imu_preprocessor", commit_hash="latest_compiled",
                                   base_dir=code_base_dir,)
    task4a = CheckoutTTRepoFromWeb(repo="tracktics-knowtion", commit_hash=fa_hash, base_dir=code_base_dir)
    task4b = CheckoutTTRepoFromWeb(repo="tt-pl-gtsam-knowtion", commit_hash=gtsam_hash, base_dir=code_base_dir)
    return {"imu": task3a, "fa": task4a, "gtsam":task4b} 
