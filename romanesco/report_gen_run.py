
from tt_backend import email as tt_email
from tt_backend.utils import Files, env
from tt_api import slack


from evaluation2 import celeryapp, celery_utils, data_discovery
from evaluation2.nb_utils import  extract_session_ids_needed_from_ipynb
from evaluation2.full_report_gen_pipeline import ReportGenerationPipeline,  ReportGenerationPipelineCommmitDiff


import requests

try:
    from requests.packages.urllib3.exceptions import SNIMissingWarning
    requests.packages.urllib3.disable_warnings(SNIMissingWarning)
    requests.packages.urllib3.disable_warnings()
except:
    pass


@celeryapp.task(bind=True)
def generate_report_end_to_end(self,fa_hash=None, gtsam_hash=None, notebook=None, force=False, output_file=None,
        results_base_dir="/tmp/", email=None, calibration_dt=None):
    task_link, task_url = celery_utils.generate_task_link(generate_report_end_to_end.request.id,
                                                          "evaluation2.report_gen_run.generate_report_end_to_end")
    tt_email.send_email("Started report generation task", task_link, email=email)

    Files.make_dir_if_not_exists(results_base_dir)
    session_ids = extract_session_ids_needed_from_ipynb(notebook)
    base_session_bin_dir = env.get_env_value("TT_EVALUATION2_DATA_HOME", optional=False)
    data = data_discovery.get_all_session_input_data(base_session_bin_dir, set(session_ids))

    multi_session_pipeline = ReportGenerationPipeline(data, fa_hash=fa_hash, gtsam_hash=gtsam_hash,
            base_dir=results_base_dir, calibration_dt=calibration_dt,
            celery_parent_task=self, notebook=notebook, output_file=output_file, force=force)
    try:
        multi_session_pipeline.run()
        tt_email.send_email("Finished report generation task", task_link, email=email)
        slack.post_to_evaluation_log("Report generation for {} succeeded: {}".format(notebook, task_url))
        return output_file
    except Exception as e:
         import traceback
         tt_email.send_email("Report generation task failed", task_link, email=email)
         slack.post_to_evaluation_log("Report generation for {} failed. Reason {} {}".format(notebook, e, traceback.format_exc()))
         raise Exception("Report generation failed with :{}".format(e))

@celeryapp.task(bind=True)
def generate_commit_difference_report(self,fa_hash1=None, fa_hash2=None, gtsam_hash=None, notebook=None, force=False, output_file=None,
        results_base_dir="/tmp/", email=None, calibration_dt=None):
    task_link, task_url = celery_utils.generate_task_link(generate_report_end_to_end.request.id,
                                                          "evaluation2.report_gen_run.generate_report_end_to_end")
    tt_email.send_email("Started report generation task", task_link, email=email)

    Files.make_dir_if_not_exists(results_base_dir)
    session_ids = extract_session_ids_needed_from_ipynb(notebook)
    base_session_bin_dir =  env.get_env_value("TT_EVALUATION2_DATA_HOME", optional=False)
    data = data_discovery.get_all_session_input_data(base_session_bin_dir, set(session_ids))

    multi_session_pipeline =  ReportGenerationPipelineCommmitDiff(data, fa_hash1=fa_hash1, fa_hash2=fa_hash2, gtsam_hash=gtsam_hash,
            base_dir=results_base_dir, calibration_dt=calibration_dt,
            celery_parent_task=self, notebook=notebook, output_file=output_file, force=force)
    try:
        multi_session_pipeline.run()
        tt_email.send_email("Finished report generation task", task_link, email=email)
        slack.post_to_evaluation_log("Report generation for {} succeeded: {}".format(notebook, task_url))
        return output_file
    except Exception as e:
         tt_email.send_email("Report generation task failed", task_link, email=email)
         slack.post_to_evaluation_log("Report generation for {} failed. Reason {}".format(notebook, e))
         raise Exception("Report generation failed with :{}".format(e))
