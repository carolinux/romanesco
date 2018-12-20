""" Some functions to format text"""
import json

def format_metadata_as_markdown(json_file, title="Metadata"):
    with open(json_file,'r') as f:
        json_str = f.read()

    d = json.loads(json_str)
    s = "### {} ### \n".format(title)
    for key, value in d.iteritems():
        s+="* **{}**: {} \n".format(key, value)
    return s

def get_markdown_from_statistics_files(statistics_files):
    s = "### Time Statistics for this run ### \n"

    for json_file in statistics_files:
        with open(json_file, 'r') as f:
            json_str = f.read()

        d = json.loads(json_str)
        stats = d["statistics"]
        output = d["output"]
        total_secs = 0
        s+="* Task with output {}\n".format(output)
        for entry in stats:
            task_name = entry["task_name"]
            secs = entry["seconds_elapsed"]
            total_secs+=secs
            if secs<60:
                time_str = "{} seconds".format(secs)
            else:
                time_str = "{} minutes {} seconds".format(secs/60, secs%60)
            s+= " * **{}**: {}\n ".format(task_name, time_str)
        if total_secs<60:
            total_time_str = "{} seconds".format(total_secs)
        else:
            total_time_str = "{} minutes {} seconds".format(total_secs/60, total_secs%60)

        s+= " * **Total**: {}\n".format(total_time_str)
    return s


def green(text):
    return '\x1b[6;30;42m' + text + '\x1b[0m'

def orange(text):
    return '\x1b[0;30;43m' + text + '\x1b[0m'

def red(text):
    return '\x1b[1;33;41m' + text + '\x1b[0m'

def blue(text):
    return '\x1b[1;32;44m' + text + '\x1b[0m'

"""
More terminal colors here:
http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
"""

YYYYMMDDHHMMSS = "%Y%m%d%H%M%S"
