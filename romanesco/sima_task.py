from tt_backend import sima_converter as sc

from tasks import FileOutputTask
from formatting import red, green, orange


class SimaConvertBin(FileOutputTask):

    def __init__(self, output_dir=None, **kwargs):
        super(SimaConvertBin, self).__init__(**kwargs)
        self.output_dir = output_dir

    def set_input_file(self, input_bin):
        self.input_fn = input_bin
        self.update_settings("input_bin", input_bin)

    def check_requirements(self):
        sima_conv_dir, sima_bin = sc.get_local_paths()
        if sima_conv_dir is None or sima_bin is None:
            print orange("Set the env vars TT_SIMA_HOME (path to sima dir) "+
            "and TT_SIMA_BIN (name of sima converter binary) to run sima converter locally. Not set, so will use the web API")
        else:
            print green("Local sima converter directory {} and binary {} found in environment variables".format(sima_conv_dir, sima_bin))


    def name(self):
        return "SimaConvertBin"

    def output(self):
        if self.output_dir is None:
            # use default naming
            return sc.get_sima_dir_from_fn(self.input_fn)
        else:
            return self.output_dir

    def _run(self):
        sima_conv_dir, sima_bin = sc.get_local_paths()
        if sima_bin and sima_conv_dir:
            local = True
            print "Have local sima converter, will use that"
        else:
            local = False
        input_fn = self.input_fn
        if local:
            sc.convert_local(input_fn, sima_conv_dir, sima_bin, target_dir=self.output(), force=True)
        else:
            sc.convert(input_fn, target_dir=self.output(), force_recompute=True)
