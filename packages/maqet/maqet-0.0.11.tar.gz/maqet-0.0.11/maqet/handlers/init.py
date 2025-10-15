from benedict import benedict

from maqet.handlers.base import Handler
# from maqet.handlers.stage import PipelineHandler as run_pipeline
from maqet.handlers.stage import StageHandler
from maqet.logger import LOG
from maqet.qemu_args import Arguments
# Legacy import - Drive class no longer exists in current storage.py
# from maqet.storage import Drive


class InitHandler(Handler):
    """
    Handles full config of maqet (basically yaml)
    """


@InitHandler.method
def binary(state, binary: str):
    LOG.debug(f'Setting binary: {binary}')
    state.binary = binary


@InitHandler.method
def arguments(state, *args):
    LOG.debug(f'Setting arguments: {args}')
    state['const_args'] = Arguments.parse_args(*args)


@InitHandler.method
def plain_arguments(state, *args):
    LOG.debug(f'Setting plain arguments: {args}')
    if 'const_args' not in state:
        state['const_args'] = []
    state['const_args'] += Arguments.split_args(*args)


@InitHandler.method
def storage(state, *args):
    if 'storage' not in state:
        state.storage = {}

    if 'const_args' not in state:
        state.const_args = []

    for drive in args:
        n = 0
        name = drive.get('name', f"drive{n}")
        while name in state.storage:
            n += 1
            name = f"drive{n}"

        # Legacy code - Drive class no longer exists
        # state.storage[name] = Drive(**drive)
        state.storage[name] = drive  # Store config dict for now

    # Legacy code - commented out as Drive class no longer exists
    # for name, drive in state.storage.items():
    #     state.const_args += drive()


@InitHandler.method
def parameters(state, **kwargs):
    LOG.debug(f'Setting parameters: {kwargs}')
    if len(kwargs) == 0:
        return
    state.parameters = kwargs


@InitHandler.method
def serial(state, *args):
    LOG.debug(f'Setting serial: {args}')
    state.serial = args


@InitHandler.method
def pipeline(state, **kwargs):
    default_stage = {'idle': {'tasks': [
        'launch',
        {'wait_for_input': {'prompt': 'Press ENTER to finish'}},
    ]}}

    state.pipeline = []
    state.procedures = []

    stages = kwargs.get('stages', {})

    if len(state._stages_to_run) == 0:
        state.pipeline.append(default_stage)
        LOG.info("Stage idle (default) added to current pipeline")
        return

    # pre_pipeline_tasks = kwargs.get('pre_pipeline_tasks', [])
    # post_pipeline_tasks = kwargs.get('post_pipeline_tasks', [])
    # pre_stage_tasks = kwargs.get('pre_stage_tasks', [])
    # post_stage_tasks = kwargs.get('post_stage_tasks', [])

    procedures = kwargs.get('procedures', {})
    state.procedures.append(procedures)
    # data._stages_to_run += ['_pre_pipeline_tasks', '_post_pipeline_tasks']

    for name, stage in stages.items():
        current_stage = stage
        current_tasks = []

        # stage.tasks = pre_stage_tasks + stage.tasks + post_stage_tasks

        if name not in state._stages_to_run:
            continue
        if 'tasks' not in stage or len(stage['tasks']) == 0:
            LOG.warn(f'Stage {name} incorrect, no tasks found. Skipping')
            continue

        # TODO: procedure that uses another procedure
        for task in stage['tasks']:
            if isinstance(task, dict):
                task_name = next(iter(task))
                if task_name == 'procedure':
                    if task['procedure'] in procedures:
                        current_tasks += procedures[task['procedure']]
                        LOG.debug(f"Procedure {task['procedure']}"
                                  " added to stage")
                    else:
                        raise Exception(f"Procedure {task['procedure']}"
                                        " not found in procedures")
                else:
                    current_tasks.append(task)
                    LOG.debug(f"Task {task_name} added to stage")
            else:
                current_tasks.append(task)
                LOG.debug(f"Task {task} added to stage")

        for task in current_tasks:
            if isinstance(task, dict):
                task = next(iter(task))
            if not StageHandler.method_exists(task):
                LOG.error(f"Task {task} not validated")
                raise Exception(f"Task {task} is invalid")
            LOG.debug(f"Task {task} validated")

        current_stage['tasks'] = current_tasks
        current_stage['arguments'] = Arguments.parse_args(
            *stage.get('arguments', [])
        ) + stage.get('plain_arguments', [])

        state.pipeline.append({name: current_stage})
        LOG.info(f"Stage {name} added to current pipeline")
