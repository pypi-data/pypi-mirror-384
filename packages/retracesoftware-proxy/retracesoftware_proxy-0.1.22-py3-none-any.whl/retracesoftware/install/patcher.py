import inspect
# from retrace_utils import _intercept
# import _intercept
import types
import re
import sys
import pdb
import builtins
import types
import functools
import traceback
import functools
import importlib
import gc
import os
import atexit
import threading
from types import SimpleNamespace, MethodType

from retracesoftware.install.typeutils import modify
# from retracesoftware.proxy.immutabletypes import ImmutableTypes
from retracesoftware.install.record import record_system
from retracesoftware.install.replay import replay_system
from retracesoftware.install.config import load_config

from functools import wraps

import retracesoftware.functional as functional
import retracesoftware.utils as utils

from retracesoftware.install import edgecases
from functools import partial
from retracesoftware.proxy.thread import start_new_thread_wrapper

# from retrace_utils.intercept import proxy

# from retrace_utils.intercept.typeutils import *
# from retrace_utils.intercept.proxytype import DynamicProxyFactory, proxytype

from retracesoftware.install.predicate import PredicateBuilder

def find_attr(mro, name):
    for cls in mro:
        if name in cls.__dict__:
            return cls.__dict__[name]

def is_descriptor(obj):
    return hasattr(obj, '__get__') or hasattr(obj, '__set__') or hasattr(obj, '__delete__')

# default_exclude = ['__class__', '__getattribute__', '__init_subclass__', '__dict__', '__del__', '__new__']

def is_function_type(cls):
    return issubclass(cls, types.BuiltinFunctionType) or issubclass(cls, types.FunctionType)

def select_keys(keys, dict):
    return {key: dict[key] for key in keys if key in dict}

def map_values(f, dict):
    return {key: f(value) for key,value in dict.items()}

def common_keys(dict, *dicts):
    common_keys = utils.set(dict)
    for d in dicts:
        common_keys &= d.keys()

    assert isinstance(common_keys, utils.set)

    return common_keys

def intersection(*dicts):
    return { key: tuple(d[key] for d in dicts) for key in common_keys(*dicts) }

def intersection_apply(f, *dicts):
    return map_values(lambda vals: f(*vals), intersection(*dicts))

def resolve(path):
    module, sep, name = path.rpartition('.')
    if module == None: module = 'builtins'
    
    return getattr(importlib.import_module(module), name)

# def sync(spec, module_dict):
#     for name,properties in spec.items():
                
#         cls = module_dict[name]

#         orig_init = cls.__init__

#         def __init__(inst, *args, **kwargs):
#             orig_init(inst, *args, **kwargs)
#             for prop in properties:
#                 self.system.add_sync(getattr(inst, prop))

def replace(replacements, coll):
    return map(lambda x: replacements.get(x, x), coll)

def container_replace(container, old, new):
    if isinstance(container, dict):
        if old in container:
            elem = container.pop(old)
            container[new] = elem
            container_replace(container, old, new)
        else:
            for key,value in container.items():
                if key != '__retrace_unproxied__' and value is old:
                    container[key] = new
        return True
    elif isinstance(container, list):
        for i,value in enumerate(container):
            if value is old:
                container[i] = new
        return True
    elif isinstance(container, set):
        container.remove(old)
        container.add(new)
        return True
    else:
        return False

def phase(func):
    func.is_phase = True  # add marker attribute
    return func

def patch(func):
    @wraps(func)
    def wrapper(self, spec, mod_dict):
        if isinstance(spec, str):
            return wrapper(self, [spec], mod_dict)
        elif isinstance(spec, list):
            res = {}
            for name in spec:
                if name in mod_dict:
                    value = func(self, mod_dict[name])
                    if value is not None:
                        res[name] = value
            return res
        elif isinstance(spec, dict):
            # return {name: func(self, mod_dict[name], value) for name, value in spec.items() if name in mod_dict}
            res = {}
            for name,value in spec.items():
                if name in mod_dict:
                    value = func(self, mod_dict[name], value)
                    if value is not None:
                        res[name] = value
            return res
        else:
            raise Exception('TODO')

    wrapper.is_phase = True  
    return wrapper

def superdict(cls):
    result = {}
    for cls in list(reversed(cls.__mro__))[1:]:
        result.update(cls.__dict__)
    
    return result

# def is_method_descriptor(obj):
#     return isinstance(obj, types.FunctionType) or \
#            (isinstance(obj, (types.WrapperDescriptorType, types.MethodDescriptorType)) and obj.__objclass__ != object)

def wrap_method_descriptors(wrapper, prefix, base):
    slots = {"__slots__": () }

    extended = type(f'{prefix}.{base.__module__}.{base.__name__}', (base,), {"__slots__": () })

    blacklist = ['__getattribute__', '__hash__', '__del__']

    for name,value in superdict(base).items():
        if name not in blacklist:
            if utils.is_method_descriptor(value):
                setattr(extended, name, wrapper(value))

    return extended

class PerThread(threading.local):
    def __init__(self):
        self.internal = utils.counter()
        self.externak = utils.counter()

class Patcher:

    def __init__(self, thread_state, config, system, 
                 immutable_types,
                 on_function_proxy = None, 
                 debug_level = 0,
                 post_commit = None):
        
        # validate(config)
        system.set_thread_id(0)
        # utils.set_thread_id(0)
        self.thread_counter = system.sync(utils.counter(1))
        # self.set_thread_number = set_thread_number

        self.thread_state = thread_state
        self.debug_level = debug_level
        self.on_function_proxy = on_function_proxy
        self.modules = config['modules']
        self.immutable_types_set = immutable_types
        self.predicate = PredicateBuilder()
        self.system = system        
        self.type_attribute_filter = self.predicate(config['type_attribute_filter'])
        self.post_commit = post_commit
        self.exclude_paths = [re.compile(s) for s in config.get('exclude_paths', [])]
        self.typepatcher = {}

        per_thread = PerThread()
        
        self.hashfunc = self.thread_state.dispatch(
            functional.constantly(None),
            internal = functional.repeatedly(functional.partial(getattr, per_thread, 'internal')),
            external = functional.repeatedly(functional.partial(getattr, per_thread, 'external')))

        def is_phase(name): return getattr(getattr(self, name, None), "is_phase", False)
        
        self.phases = [(name, getattr(self, name)) for name in Patcher.__dict__.keys() if is_phase(name)]

    def log(self, *args):
        self.system.tracer.log(*args)

    def path_predicate(self, path):
        for exclude in self.exclude_paths:
            if exclude.match(str(path)) is not None:
                # print(f'in path_predicate, excluding {path}')
                return False
        return True

    def on_proxytype(self, cls):

        def patch(spec):
            for method, transform in spec.items():                
                setattr(cls, method, resolve(transform)(getattr(cls, method)))

        if cls.__module__ in self.modules:
            spec = self.modules[cls.__module__]

            if 'patchtype' in spec:
                patchtype = spec['patchtype']
                if cls.__name__ in patchtype:
                    patch(patchtype[cls.__name__])

    @property
    def disable(self):
        return self.thread_state.select('disabled')
    
    def proxyable(self, name, obj):
        if name.startswith('__') and name.endswith('__'):
            return False
        
        if isinstance(obj, (str, int, dict, list, tuple)):
            return False
        
        if isinstance(obj, type):
            return not issubclass(obj, BaseException) and obj not in self.immutable_types_set
        else:
            return type(obj) not in self.immutable_types_set

    @phase
    def immutable_types(self, spec, mod_dict):
        if isinstance(spec, str):
            return self.immutable_types([spec], mod_dict)

        for name in spec:
            if name in mod_dict:
                if isinstance(mod_dict[name], type):
                    assert isinstance(mod_dict[name], type)
                    self.immutable_types_set.add(mod_dict[name])
                else:
                    raise Exception(f'Tried to add "{name}" - {mod_dict[name]} which isn\'t a type to immutable')

    @patch
    def proxy(self, value):
        return self.system(value)

    @phase
    def proxy_all_except(self, spec, mod_dict):

        all_except = set(spec)

        def proxyable(name, value):
            return name not in all_except and self.proxyable(name, value)
        
        return {key: self.system(value) for key,value in mod_dict.items() if proxyable(key, value)}

    @phase
    def proxy_type_attributes(self, spec, mod_dict):
        for classname, attributes in spec.items():
            if classname in mod_dict:
                cls = mod_dict[classname]
                if isinstance(cls, type):
                    for name in attributes:
                        attr = find_attr(cls.__mro__, name)
                        if attr is not None and (callable(attr) or is_descriptor(attr)):
                            proxied = self.system(attr)
                            # proxied = self.proxy(attr)

                            with modify(cls):
                                setattr(cls, name, proxied)
                else:
                    raise Exception(f"Cannot patch attributes for {cls.__module__}.{cls.__name__} as object is: {cls} and not a type")

    @phase
    def replace(self, spec, mod_dict):
        return {key: resolve(value) for key,value in spec.items()}

    @patch
    def patch_start_new_thread(self, value):
        return start_new_thread_wrapper(thread_state = self.thread_state, 
                                        on_exit = self.system.on_thread_exit,
                                        start_new_thread = value)
    
        # def start_new_thread(function, *args):
        #     # synchronized, replay shoudl yield correct number
        #     thread_id = self.thread_counter()

        #     def threadrunner(*args, **kwargs):
        #         nonlocal thread_id
        #         self.system.set_thread_id(thread_id)
                
        #         with self.thread_state.select('internal'):
        #             try:
        #                 # if self.tracing:
        #                 #     FrameTracer.install(self.thread_state.dispatch(noop, internal = self.checkpoint))    
        #                 return function(*args, **kwargs)
        #             finally:
        #                 print(f'exiting: {thread_id}')

        #     return value(threadrunner, *args)

        # return self.thread_state.dispatch(value, internal = start_new_thread)

    @phase
    def wrappers(self, spec, mod_dict): 
        return intersection_apply(lambda path, value: resolve(path)(value), spec, mod_dict)

    @patch
    def patch_exec(self, exec):

        def is_module(source, *args):
            return isinstance(source, types.CodeType) and source.co_name == '<module>'
        
        def after_exec(source, globals = None, locals = None):
            self(sys.modules[globals['__name__']])
        
        def first(x): return x[0]
            
        def disable(func): return self.thread_state.wrap('disabled', func)
    
        return self.thread_state.dispatch(
            exec, 
            internal = functional.sequence(
                functional.vector(exec, functional.when(is_module, disable(after_exec))), first))
    
    # self.thread_state.wrap(desired_state = 'disabled', function = exec_wrapper)

    @patch
    def sync_types(self, value):
        return wrap_method_descriptors(self.system.sync, "retrace", value)

    @phase
    def with_state_recursive(self, spec, mod_dict):

        updates = {}

        for state,elems in spec.items():

            def wrap(obj): 
                return functional.recurive_wrap_function(
                    functional.partial(self.thread_state.wrap, state),
                    obj)
            
            updates.update(map_values(wrap, select_keys(elems, mod_dict)))
        
        return updates

    @phase
    def methods_with_state(self, spec, mod_dict):

        # updates = {}

        def update(cls, name, f):
            setattr(cls, name, f(getattr(cls, name)))

        for state,cls_methods in spec.items():
            def wrap(obj): 
                assert callable(obj)
                return self.thread_state.wrap(desired_state = state, function = obj)

            for typename,methodnames in cls_methods.items():
                cls = mod_dict[typename]

                for methodname in methodnames:
                    update(cls, methodname, wrap)
        
        return {}

    @phase
    def with_state(self, spec, mod_dict):

        updates = {}

        for state,elems in spec.items():

            def wrap(obj): 
                return self.thread_state.wrap(desired_state = state, function = obj)

            updates.update(map_values(wrap, select_keys(elems, mod_dict)))
        
        return updates

    @patch
    def patch_hash(self, cls):
        utils.patch_hash(cls = cls, hashfunc = self.hashfunc)

    @patch
    def patch_extension_exec(self, exec):
        
        def first(x): return x[0]

        def disable(func): return self.thread_state.wrap('disabled', func)
    
        return self.thread_state.dispatch(exec, 
                                   internal = functional.sequence(functional.vector(exec, disable(self)), first))
        
        # def wrapper(module):
        #     with self.thread_state.select('internal'):
        #         res = exec(module)

        #     self(module)
        #     return res

        # return wrapper

    @patch
    def path_predicates(self, func, param):
        signature = inspect.signature(func).parameters

        try:
            index = list(signature.keys()).index(param)
        except ValueError:
            print(f'parameter {param} not in: {signature.keys()} {type(func)} {func}')
            raise
        
        param = functional.param(name = param, index = index)

        assert callable(param)
        
        return functional.if_then_else(
            test = functional.sequence(param, self.path_predicate),
            then = func, 
            otherwise = self.thread_state.wrap('disabled', func)) 
        
    @phase
    def wrap(self, spec, mod_dict):
        updates = {}

        for path, wrapper_name in spec.items():

            parts = path.split('.')
            name = parts[0]
            if name in mod_dict:
                value = mod_dict[name]
                assert not isinstance(value, utils.wrapped_function), \
                    f"value for key: {name} is already wrapped"
                
                if len(parts) == 1:
                    updates[name] = resolve(wrapper_name)(value)
                elif len(parts) == 2:
                    member = getattr(value, parts[1], None)
                    if member:
                        new_value = resolve(wrapper_name)(member)
                        setattr(value, parts[1], new_value)
                else:
                    raise Exception('TODO')
                
        return updates
                        
    def updates(self, spec, mod_dict):
        updates = {}

        for phase,func in self.phases:
            if phase in spec:
                self.log('install.module.phase', phase)
                
                phase_updates = func(spec[phase], mod_dict | updates)

                if phase_updates:
                    self.log('install.module.phase.results', list(phase_updates.keys()))
                    for name,value in phase_updates.items():
                        if value is not None:
                            updates[name] = value
                    # updates |= phase_updates
                
        return updates

    def configs(self, module):
        for name,value in sys.modules.items():
            if value is module and name in self.modules:
                yield name

    def patch_module_with_name(self, mod_name, module):
        with self.disable:

            assert self.thread_state.value == 'disabled'

            self.log('install.module', mod_name)

            # self.system.log(f'patching module: {mod_name}')

            spec = self.modules.get(mod_name)

            updates = self.updates(spec = spec, mod_dict = module.__dict__)

            originals = select_keys(updates.keys(), module.__dict__)

            module.__dict__.update(updates)

            for name, value in originals.items():
                for ref in gc.get_referrers(value):
                    if ref is not originals:
                        container_replace(container = ref, old = value, new = updates[name])
                if isinstance(updates[name], type) and isinstance(value, type) and issubclass(updates[name], value):
                    for subclass in value.__subclasses__():
                        if subclass not in updates.values():
                            subclass.__bases__ = tuple(replace({value: updates[name]}, subclass.__bases__))

            module.__retrace__ = originals

            if self.post_commit:
                self.post_commit(mod_name, updates)

    def __call__(self, module):
                
        if not hasattr(module, '__retrace__'):

            configs = list(self.configs(module))

            if len(configs) > 0:
                if len(configs) > 1:
                    raise Exception(f'TODO')
                else:
                    module.__retrace__ = None
                    try:
                        self.patch_module_with_name(configs[0], module)
                    except Exception as error:
                        raise Exception(f'Error patching module: {configs[0]}') from error

        return module
    
def env_truthy(key, default=False):
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")

class ImmutableTypes(set):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __contains__(self, item):
        assert isinstance(item, type)

        if super().__contains__(item):
            return True

        for elem in self:
            if issubclass(item, elem):
                self.add(item)
                return True

        return False            

def install(mode):

    create_system = None

    if mode == 'record':
        create_system = record_system
    elif mode == 'replay':
        create_system = replay_system
    else:
        raise Exception(f'mode: {mode} unsupported')
    
    importlib.import_module('locale')
    importlib.import_module('calendar')
    importlib.import_module('_strptime')

    config = load_config('config.json')

    states = [x for x in config['states'] if isinstance(x, str)]

    thread_state = utils.ThreadState(*states)

    immutable_types = ImmutableTypes()

    if 'RETRACE_RECORDING_PATH' in os.environ:
        config['recording_path'] = os.environ['RETRACE_RECORDING_PATH']

    # immutable_types = ImmutableTypes(config)
    config['verbose'] = env_truthy('RETRACE_VERBOSE')

    system = create_system(thread_state = thread_state,
                           immutable_types = immutable_types,
                           config = config)

    os.register_at_fork(before = system.before_fork, 
                        after_in_parent = system.after_fork_in_parent,
                        after_in_child = system.after_fork_in_child)
    
    patcher = Patcher(thread_state = thread_state,
                      config = config,
                      system = system,
                      post_commit = getattr(system, 'on_patched', None),
                      immutable_types = immutable_types)
    
    system.on_proxytype = patcher.on_proxytype

    def at_exit(): thread_state.value = 'disabled'

    # print(f'MODULES: {list(sys.modules.keys())}')

    importlib.invalidate_caches()

    # with thread_state.select('internal'):

    atexit.register(lambda: at_exit)
    
    for key, module in list(sys.modules.items()):
        if not key.startswith('retracesoftware'):
            patcher(module)

    for library in config.get('preload', []):
        with thread_state.select('internal'):
            importlib.import_module(library)

    importlib.invalidate_caches()
    # # if env_truthy('RETRACE_TRACE_CALLS'):
    # #     trace_calls(system = retracesystem)

    # thread_state.value = 'internal'

    # import threading
    # threading.current_thread().retrace = system

    threading.current_thread().__retrace__ = system

    # original = atexit.register

    # def atexit_register(function):
    #     return original(thread_state.wrap('internal', function))

    def wrap_internal(func): return thread_state.wrap('internal', func)

    atexit.register = \
        thread_state.dispatch(atexit.register, internal = functional.sequence(wrap_internal, atexit.register))

    def disable_after_main(frame):
        if system.is_entry_frame(frame):
            print('enabling retrace!!!!')
            # utils.intercept_frame_eval(None)
            thread_state.value = 'internal'
            
            def on_return(): 
                thread_state.value = 'disabled'

            obj = SimpleNamespace()
            obj.on_return = on_return

            return obj
        else:
            return disable_after_main

    utils.intercept_frame_eval(disable_after_main)

    # utils.sigtrap(None)
    print(f'retrace installed: {thread_state}')
    return system
