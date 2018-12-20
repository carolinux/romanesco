import os

from tt_api import calibration as tt_cal
from tt_backend.utils import setup_json_calib_file

from tasks import FileOutputTask
import formatting

class DownloadCalibrationValues(FileOutputTask):

    def __init__(self, base_dir="", tracker_id="", use_calibration_before=None, **kwargs):
        super(DownloadCalibrationValues, self).__init__(**kwargs)
        self.base_dir = base_dir
        print formatting.green("Getting latest calibration date as part of initialization. If this hangs, check that calibration.tracktics.zone:5000/cal is responding, restart may be required.")
        self.latest_date_of_calibration_values = tt_cal.get_latest_datetime_with_calibration_for_tracker(tracker_id,
                dt=use_calibration_before)
        print formatting.green("Got latest date: {}".format(self.latest_date_of_calibration_values))
        self.tracker_id = tracker_id
        self.update_settings("calibration_max_date", self.latest_date_of_calibration_values.strftime(formatting.YYYYMMDDHHMMSS))
        self.update_settings("tracker_id", self.tracker_id)

    def name(self):
        return "DownloadCalibrationValues"

    def _run(self):
        tracker_id = self.tracker_id
        acc_calib = tt_cal.get_calibration(tracker_id, "acc", datetime=self.latest_date_of_calibration_values, as_dict=True)
        gyr_calib = tt_cal.get_calibration(tracker_id, "gyr", datetime=self.latest_date_of_calibration_values, as_dict=True)
        mag_calib = tt_cal.get_calibration(tracker_id, "mag", datetime=self.latest_date_of_calibration_values, as_dict=True)
        calibration_dict = setup_json_calib_file.get_default_calibration()
        setup_json_calib_file.perturb_calibration(calibration_dict, **acc_calib)
        setup_json_calib_file.perturb_calibration(calibration_dict, **gyr_calib)
        setup_json_calib_file.perturb_calibration(calibration_dict, **mag_calib)
        setup_json_calib_file.perturb_calibration(calibration_dict, tracker_id=tracker_id)
        setup_json_calib_file.export_calibration_json(calibration_dict, self.output())

    def output(self):
        return os.path.join(self.base_dir,
                "calibration_{}_{}.json".format(self.tracker_id,
                    self.latest_date_of_calibration_values.strftime(formatting.YYYYMMDDHHMMSS)))

