import os

from tt_backend.utils import Files, filenames

from tasks import FileOutputTask
from formatting import red, green, orange


class SymlinkGroundTruth(FileOutputTask):
    """Symlinks any ground truth files found in a directory to another directory with the same names"""

    def __init__(self, in_dir, out_dir, **kwargs):

        super(SymlinkGroundTruth, self).__init__(**kwargs)
        self.in_dir = in_dir
        self.out_dir = out_dir
        self.update_settings("directory_with_ground_truth", self.in_dir)


    def name(self):
        return "SymlinkGroundTruth"

    def output(self):
        # Creates an empty file to signify success
        return os.path.join(self.out_dir, "GROUND_TRUTH_SYMLINK_SUCCESS")

    def _run(self):
        Files.symlink_everything(self.in_dir, self.out_dir, filenames_to_skip=set(filenames.IMU_PP_FNS+
                                                                                  filenames.SIMA_FNS))
        open(self.output(), 'a').close()
