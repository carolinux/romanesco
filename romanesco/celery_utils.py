from datetime import datetime


def get_status_for_group_of_tasks(group_async_res):
    """
    Creates a generator to get the status of the group of celery tasks which run in parallel
    This generator should be called periodically to check the status.

    Example:
        There is an example in evaluation2.report_gen_run

    Args:
        group_async_res(celery.result.GroupResult): The group result we want to inspect

    Yields:
        tuple(boolean, str): Whether the whole group has finished, and a string with all the children statuses

    Raises:
        Exception: If the group has finished and any of the tasks in the group have failed

    """

    while True:
        states = []
        for child in group_async_res.children:
            if child.info:
                states.append(child.state+" with info: "+str(child.info))
            else:
                states.append(child.state)

        yield False, '\n'.join(states)
        if group_async_res.ready():
            for child in group_async_res.children:
                if child.state == "FAILURE":
                    raise Exception("At least one of the sessions failed with : {}".format(child.info))
            yield True, '\n'.join(states)


def generate_task_meta():
    start_dt = datetime.now()
    return {"start":start_dt, "statuses":[]}


def generate_task_link(task_id, task_name):
    # this needs to be consistent with routing as defined in evaluation_app/web.py
    url = "http://evaluation.tracktics.zone:5000/status2/{}/{}".format(task_name, task_id)
    return "View <a href={}>here</a>".format(url), url

