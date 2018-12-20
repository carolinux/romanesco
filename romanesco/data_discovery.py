import os

from tt_backend.utils import Fn

def get_all_session_input_data(base_folder, session_ids_to_match=None):
    """" Returns all the session data stored in the filesystem that matches a set of session ids.


    data is stored like this: (take a look also at evaluation.tracktics.zone:/home/ubuntu/eval_data)
    base_folder/subfolder1/session_fUqpW-00dgEKsvWZ/session_fUqpW-00dgEKsvWZ.bin
    base_folder/subfolder1/ssession_fUqpW-01dgEKsvWZ/ession_fUqpW-01dgEKsvWZ.bin
    base_folder/subfolder2/session_UBPup-01UX7BloPS/session_UBPup-01UX7BloPS.bin

    then it would return a list of tuples with (raw_bin_path, sima_directory_path, tracker_id)  as follows:
    [(base_folder/subfolder1/session_fUqpW-00dgEKsvWZ/session_fUqpW-00dgEKsvWZ.bin, base_folder/subfolder1/session_fUqpW-00dgEKsvWZ, fUqpW),
    (base_folder/subfolder1/session_fUqpW-01dgEKsvWZ/session_fUqpW-00dgEKsvWZ.bin, base_folder/subfolder1/session_fUqpW-01dgEKsvWZ, fUqpW),
    (base_folder/subfolder2/session_UBPup-01UX7BloPS/session_UBPup-01UX7BloPS.bin, base_folder/subfolder2/session_UBPup-01UX7BloPS/, UBPup)] 
    """

    res = []
    experiment_dirs = Fn.getChildrenDirectories(base_folder)
    if session_ids_to_match is None:
        return_all_sessions_found = True
    else:
        return_all_sessions_found = False

    for directory in experiment_dirs:
        sima_directories = Fn.getChildrenDirectories(directory)
        for sima_directory in sima_directories:
            _, session_id,_ = Fn.fileparts(sima_directory)
            if not return_all_sessions_found and session_id not in session_ids_to_match:
                continue
            tracker_id = session_id[8:13]
            res.append((os.path.join(sima_directory, session_id+".bin"), sima_directory, tracker_id))
    return res
