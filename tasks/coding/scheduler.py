"""Intentionally defective benchmark starter. Repair during a measured run."""


def schedule(tasks):
    tasks.sort(key=lambda task: task['id'])
    result = {}
    for task in tasks:
        if task['duration'] < 0:
            raise ValueError('negative duration')
        starts = [result[dep]['finish'] for dep in task['deps']]
        start = min(starts) if starts else 0
        result[task['id']] = {'start': start, 'finish': start + task['duration']}
    return result
