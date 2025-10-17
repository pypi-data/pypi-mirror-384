from delta.runners.run import DeltaRun, get
from delta.exceptions.runners import DeltaRunnerError, DeltaRunnerNotFound


def create(model: dict) -> DeltaRun:
    if 'type' not in model:
        raise DeltaRunnerError('Missing required runner type: "type"')

    runner_name = model['type']
    try:
        runner_factory_class = get(runner_name)
    except KeyError:
        raise DeltaRunnerNotFound(f'Unknown runner type: "{runner_name}"')

    runner = runner_factory_class(model.get('parameters'))
    return runner
