from retracesoftware.proxy import *

import retracesoftware.functional as functional
import retracesoftware_utils as utils
import retracesoftware.stream as stream

from retracesoftware.install.tracer import Tracer
from retracesoftware.install import globals

import os
import sys
from datetime import datetime
import json
from pathlib import Path

# class ThreadSwitch:
#     def __init__(self, id):
#         self.id = id
    
#     def __repr__(self):
#         return f'ThreadSwitch<{self.id}>'

#     def __str__(self):
#         return f'ThreadSwitch<{self.id}>'

def write_files(recording_path):
    with open(recording_path / 'env', 'w') as f:
        json.dump(dict(os.environ), f, indent=2)

    with open(recording_path / 'exe', 'w') as f:
        f.write(sys.executable)

    with open(recording_path / 'cwd', 'w') as f:
        f.write(os.getcwd())

    with open(recording_path / 'cmd', 'w') as f:
        json.dump(sys.orig_argv, f, indent=2)

def create_recording_path(path):
    expanded = datetime.now().strftime(path.format(pid = os.getpid()))
    os.environ['RETRACE_RECORDING_PATH'] = expanded
    return Path(expanded)

def tracing_level(config):
    return os.environ.get('RETRACE_DEBUG', config['default_tracing_level'])

# def tracing_config(config):
#     level = os.environ.get('RETRACE_DEBUG', config['default_tracing_level'])
#     return config['tracing_levels'].get(level, {})

def merge_config(base, override):
    if isinstance(base, dict) and isinstance(override, dict):
        ...
    else:
        return override


def record_system(thread_state, immutable_types, config):

    recording_path = create_recording_path(config['recording_path'])

    recording_path.mkdir(parents=True, exist_ok=True)

    globals.recording_path = globals.RecordingPath(recording_path)

    write_files(recording_path)

    tracing_config = config['tracing_levels'].get(tracing_level(config), {})

    with open(recording_path / 'tracing_config.json', 'w') as f:
        json.dump(tracing_config, f, indent=2)

    def write_main_path(path):
        with open(recording_path / 'mainscript', 'w') as f:
            f.write(path)

    # writer = stream.writer(path = recording_path / 'trace.bin')
    
    # os.register_at_fork(
    #     # before = self.thread_state.wrap('disabled', self.before_fork),
    #     before = before,
    #     after_in_parent = self.thread_state.wrap('disabled', self.after_fork_in_parent),
    #     after_in_child = self.thread_state.wrap('disabled', self.after_fork_in_child))

    # self.writer = thread_state.wrap(
    #     desired_state = 'disabled',
    #     sticky = True,
    #     function = VerboseWriter(writer)) if verbose else writer

    # def gc_start(self):
    #     self.before_gc = self.thread_state.value
    #     self.thread_state.value = 'external'

    # def gc_end(self):
    #     self.thread_state.value = self.before_gc
    #     del self.before_gc

    # def gc_hook(self, phase, info):
    #     if phase == 'start':
    #         self.gc_start()

    #     elif phase == 'stop':
    #         self.gc_end()
    # gc.callbacks.append(self.gc_hook)

    # print(f'Tracing config: {tracing_config(config)}')

    # tracer = Tracer(config = tracing_config(config), writer = writer.handle('TRACE'))

    return RecordProxySystem(thread_state = thread_state,
                             immutable_types = immutable_types, 
                             tracing_config = tracing_config,
                             write_main_path = write_main_path,
                             path = recording_path / 'trace.bin')
