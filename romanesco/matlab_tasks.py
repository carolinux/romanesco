import os


from tt_backend.utils import filenames, env, Files
from tt_backend.utils import pipeline # matlab pipeline utilities

from tasks import FileOutputTask

class MatlabTask(object):

    def matlab_home(self):
        # when not having a matlab installation, it should be the runtime, ie something like:
        # /usr/local/MATLAB/MATLAB_Runtime/v901/
        return env.get_env_value('MATLAB_HOME', optional=False)

    def get_matlab_directory_for_so_files(self):
        ml_home = self.matlab_home()
        return os.path.join(ml_home, "sys", "opengl", "lib", "glnxa64")

    def format_directory_for_matlab(self, directory):
        # sometimes we have issues combining paths
        if not directory.endswith("/"):
            return directory+"/"
        else:
            return directory


class ImuPreprocess(FileOutputTask, MatlabTask):

    def __init__(self, imu_pp_code_directory="", sima_dir=None, matlab_installed=True, calibration_json="",
                 **kwargs):
        """ 
        Args:
            use_calibration_before: Datetime. Calibration values need to have a date in the database that is before this date
            matlab_installed: If true, run the code via matlab. If not, launch a compiled binary
        """
        super(ImuPreprocess, self).__init__(**kwargs)
        self.matlab_installed = matlab_installed
        # keep track of this
        self.update_settings("matlab_installed", self.matlab_installed)
        self.sima_dir = sima_dir
        self.imu_pp_code_directory = imu_pp_code_directory
        self.calibration_json = calibration_json


    def name(self):
        return "ImuPreprocessor"

    def output(self):
        """Returns the imu pp directory (with symlinked sima)"""
        return self.sima_dir+"_imupp_"+self.checksum()[:10]

    def _run(self):
        sima_directory = self.sima_dir
        imu_pp_directory = self.output()
        Files.make_dir_if_not_exists(imu_pp_directory)
        Files.create_symlinks(sima_directory, imu_pp_directory, filenames.SIMA_FNS, silently_skip_if_src_not_exists=True)
        args = [self.format_directory_for_matlab(sima_directory),
                self.format_directory_for_matlab(imu_pp_directory), self.calibration_json]
        if self.matlab_installed:
            preprocessor_code_directory = os.path.join(self.imu_pp_code_directory, "IMU_preprocessor")
            pipeline.run_matlab_batch_mode("main", self.matlab_home(), preprocessor_code_directory, args=args)
        else:
            # try compiled matlab
            shell_script = os.path.join(self.imu_pp_code_directory, "main", "for_testing", "run_main.sh") 
            pipeline.run_matlab_shell_script(shell_script, self.matlab_home(), *args)

class FuseKnowtion(FileOutputTask, MatlabTask):

    def __init__(self, fa_knowtion_code_directory="", sima_dir=None, gtsam_dir=None,matlab_installed=True,**kwargs):

        super(FuseKnowtion, self).__init__(**kwargs)
        self.matlab_installed = matlab_installed
        self.sima_dir = sima_dir # this directory should also have the imu preprocessed files
        self.fa_knowtion_code_directory = fa_knowtion_code_directory
        self.gtsam_dir = gtsam_dir
        # TODO: Have the option to use custom params for fa
        # And add the checksum of the params file to the settings
        # in which case, the output should also be affected


    def name(self):
        return "FusionAlgorithmKnowtion"

    def output(self):
        """Returns the fa directory (with symlinked sima and imu)"""
        fa_hash = self.settings()["tracktics-knowtion_commit_hash"]
        # TODO: Write function to get settings and allow "missing" or unknown
        #max_date = self.settings()["calibration_max_date"]
        return self.sima_dir+"_fahash_"+fa_hash+"_faparam_checksum_"+self.checksum()[:10]

    def add_gtsam_to_matlab_path(self):
        # add the gtsam library to the matlab bin path
        # FIXME: This might create issues if multiple processes are trying to set multiple ones
        # at the same time
        if os.path.exists(self.get_symlink_path_for_gtsam_so()):
            try:
                os.unlink(self.get_symlink_path_for_gtsam_so())
            except:
                # Can get timing errors here
                pass
        print("Creating symlink from {} to {}".format(self.get_gtsam_so(), self.get_symlink_path_for_gtsam_so()))
        os.system('ln -sf  {} {}'.format(self.get_gtsam_so(), self.get_symlink_path_for_gtsam_so()))

    def _run(self):
        sima_directory = self.sima_dir
        self.add_gtsam_to_matlab_path()
        fa_directory = self.output()
        Files.make_dir_if_not_exists(fa_directory)
        Files.create_symlinks(sima_directory, fa_directory, filenames.SIMA_FNS + filenames.IMU_PP_FNS, silently_skip_if_src_not_exists=True)
        output_fused = os.path.join(fa_directory, filenames.FUSION_RESULTS_FN)
        args = [self.format_directory_for_matlab(sima_directory), output_fused]
        if self.matlab_installed:
            pipeline.run_matlab_batch_mode("entryPoint", self.matlab_home(),
                    self.fa_knowtion_code_directory, args=args,
                    run_before_matlab=self.load_gtsam_cmd())
        else:
            shell_script = os.path.join(self.fa_knowtion_code_directory, "fa_knowtion", "for_testing", "run_fa_knowtion.sh") 
            pipeline.run_matlab_shell_script(shell_script, self.matlab_home(), *args)

    def get_gtsam_home(self):
        return self.gtsam_dir

    def load_gtsam_cmd(self):
        cmd = """addpath('{}');""".format(os.path.join(self.get_gtsam_home(), "gtsam", "gtsam_toolbox"))
        return cmd

    def get_gtsam_so(self):
        return os.path.join(self.get_gtsam_home(), "gtsam", "lib","libgtsam.so.3")

    def get_symlink_path_for_gtsam_so(self):
        return os.path.join(self.get_matlab_directory_for_so_files(), "libgtsam.so.3")
