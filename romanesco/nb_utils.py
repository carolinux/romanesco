""" Functions to read and write stuff from and to and generate notebooks"""
import codecs
import os
import subprocess
import shutil

import nbformat
from nbformat import current as nbf

from nbparameterise import nbparameterise as nbparam
from tt_backend.utils import env, Fn

from evaluation2 import formatting as fmt

def extract_session_ids_needed_from_ipynb(notebook_template):
    return read_variable_value(notebook_template, code_cell=1, variable_name="datasets")

def read_variable_value(ipynb, code_cell=1, variable_name="datasets"):
    """Return the value of a variable defined in a code_cell in an ipython notebook"""
    with open(ipynb) as f:
        nb = nbformat.read(f, as_version=4)

    orig_parameters = nbparam.extract_parameters(nb, n=code_cell)
    found = False
    for param in orig_parameters:
        if param.name == variable_name:
            value = param.value
            found = True
            break
    if not found:
        raise Exception("Could not find variable with name {} in code cell {}".format(variable_name, code_cell))
    return value

def overwrite_variable_values(ipynb_template, ipynb_out, code_cell, value_dict, execute=True):
    """ Writes out the template to outfile with the variables overriden in the specified cell """
    with open(ipynb_template) as f:
        nb = nbformat.read(f, as_version=4)
    orig_parameters = nbparam.extract_parameters(nb, n=code_cell)
    params = nbparam.parameter_values(orig_parameters, **value_dict)
    new_nb = nbparam.replace_definitions(nb, params, execute=execute, n=code_cell)
    with codecs.open(ipynb_out, 'w', encoding='utf-8') as f:
       nbformat.write(new_nb, f)

def add_custom_text(ipynb_out, text="test text", insert_index=1):
    with open(ipynb_out) as f:
            nb = nbformat.read(f, as_version=4)
    metadata_cell = nbf.new_text_cell('markdown', text)
    nb.cells = nb.cells[:insert_index] + [metadata_cell] + nb.cells[insert_index:]
    with codecs.open(ipynb_out, 'w', encoding='utf-8') as f:
       nbformat.write(nb, f)

def overwrite_input_folders_and_generate(notebook_template, output_html, replace_dict, statistics_files=None):
    """ Replace dict has the variable names as the keys and the values of those variables as the values """
    output_ipynb = output_html+".ipynb"
    overwrite_variable_values(notebook_template, output_ipynb, code_cell=2,
            value_dict=replace_dict, execute=False)
    metadata_file = replace_dict["input_folders"][0]+".meta"
    add_custom_text(output_ipynb, insert_index=1, text=fmt.format_metadata_as_markdown(metadata_file,
                                                                                       title="Metadata of first session processed"))
    if len(replace_dict["input_folders"])>1:
        metadata_file = replace_dict["input_folders"][1]+".meta"
        add_custom_text(output_ipynb, insert_index=2, text=fmt.format_metadata_as_markdown(metadata_file,
                                title="Metadata of second session processed or second commit processed"))
 
    if statistics_files is not None:
        add_custom_text(output_ipynb, insert_index=1, text=fmt.get_markdown_from_statistics_files(statistics_files))
    generate_html(output_ipynb, output_html)

def generate_html(ipynb, output_html):
    cmd = ["jupyter", "nbconvert", "--ExecutePreprocessor.timeout=100000", "--output", output_html,
                                "--execute", ipynb,"--to", "html"]
    cmd2 = " ".join(cmd)
    try:
        subprocess.check_call(cmd2, shell=True)
    except Exception as e:
        tt_webtools_home = env.get_env_value("TT_WEBTOOLS_HOME", optional=True)
        if tt_webtools_home is not None:
            _, fn, ext = Fn.fileparts(ipynb)
            new_ipynb = os.path.join(tt_webtools_home, "notebooks", "dashboard", fn+ext)
            shutil.copy(ipynb, new_ipynb)
            raise Exception("Command: {} failed. Notebook has been copied to <a href={}>jupyter</a> for inspection"
            .format(cmd2, "http://evaluation.tracktics.zone:8888/notebooks/"+fn+ext))
        else:
            raise Exception("Command: {} failed.".format(cmd2))
