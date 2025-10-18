import retracesoftware.functional as functional
import retracesoftware_utils as utils
import types
from retracesoftware.proxy.gateway import adapter_pair
from types import SimpleNamespace
from retracesoftware.proxy.proxytype import *
from retracesoftware.proxy.stubfactory import Stub
from retracesoftware.install.typeutils import modify, WithFlags

import sys
import gc

class RetraceError(Exception):
    pass

def proxy(proxytype):
    return functional.spread(
        utils.create_wrapped,
        functional.sequence(functional.typeof, proxytype),
        None)

def maybe_proxy(proxytype):
    return functional.if_then_else(
            functional.isinstanceof(utils.Wrapped),
            utils.unwrap,
            proxy(functional.memoize_one_arg(proxytype)))

unproxy_execute = functional.mapargs(starting = 1, 
                                     transform = functional.walker(utils.try_unwrap), 
                                     function = functional.apply)

def resolve(obj):
    try:
        return getattr(sys.modules[obj.__module__], obj.__name__)
    except:
        return None

def is_function_type(cls):
    return cls in [types.BuiltinFunctionType, types.FunctionType]

method_types = (types.MethodDescriptorType,
                types.WrapperDescriptorType,
                types.FunctionType)

def is_instance_method(obj):
    return isinstance(obj, method_types)

class ProxySystem:
    
    def bind(self, obj): pass

    def wrap_int_to_ext(self, obj): return obj
    
    def wrap_ext_to_int(self, obj): return obj
    
    def on_int_call(self, func, *args, **kwargs):
        pass

    def on_ext_result(self, result):
        pass

    def on_ext_error(self, err_type, err_value, err_traceback):
        pass
        
    # def stacktrace(self):
    #     self.tracer.stacktrace()

    def set_thread_id(self, id):
        utils.set_thread_id(id)

    def __init__(self, thread_state, immutable_types, tracer):
        
        self.thread_state = thread_state
        self.fork_counter = 0
        self.tracer = tracer
        self.immutable_types = immutable_types
        self.on_proxytype = None
        
        def is_immutable_type(cls):
            return cls is object or issubclass(cls, tuple(immutable_types))

        is_immutable = functional.sequence(functional.typeof, functional.memoize_one_arg(is_immutable_type))

        def proxyfactory(proxytype):
            return functional.walker(functional.when_not(is_immutable, maybe_proxy(proxytype)))

        int_spec = SimpleNamespace(
            apply = thread_state.wrap('internal', functional.apply),
            proxy = proxyfactory(thread_state.wrap('disabled', self.int_proxytype)),
            on_call = tracer('proxy.int.call', self.on_int_call),
            on_result = tracer('proxy.int.result'),
            on_error = tracer('proxy.int.error'),
        )
        
        ext_spec = SimpleNamespace(
            apply = thread_state.wrap('external', functional.apply),
            proxy = proxyfactory(thread_state.wrap('disabled', self.ext_proxytype)),
            on_call = tracer('proxy.ext.call'),
            on_result = self.on_ext_result,
            on_error = self.on_ext_error,
        )

        int2ext, ext2int = adapter_pair(int_spec, ext_spec)

        def gateway(name, internal = functional.apply, external = functional.apply):
            default = tracer(name, unproxy_execute)
            return thread_state.dispatch(default, internal = internal, external = external)

        self.ext_handler = thread_state.wrap('retrace', self.wrap_int_to_ext(int2ext))
        self.int_handler = thread_state.wrap('retrace', self.wrap_ext_to_int(ext2int))

        self.ext_dispatch = gateway('proxy.int.disabled.event', internal = self.ext_handler)
        self.int_dispatch = gateway('proxy.ext.disabled.event', external = self.int_handler)

        if 'systrace' in tracer.config:
            func = thread_state.wrap(desired_state = 'disabled', function = tracer.systrace)
            func = self.thread_state.dispatch(lambda *args: None, internal = func)
            sys.settrace(func)

        tracer.trace_calls(thread_state)

    def new_child_path(self, path):
        return path.parent / f'fork-{self.fork_counter}' / path.name

    def before_fork(self):
        self.saved_thread_state = self.thread_state.value
        self.thread_state.value = 'disabled'

    def after_fork_in_child(self):
        self.thread_state.value = self.saved_thread_state
        self.fork_counter = 0

    def after_fork_in_parent(self):
        self.thread_state.value = self.saved_thread_state
        self.fork_counter += 1

    def on_thread_exit(self, thread_id):
        pass

    # def create_stub(self): return False
        
    def int_proxytype(self, cls):
        if cls is object:
            breakpoint()

        proxytype = dynamic_int_proxytype(
                handler = self.int_dispatch,
                cls = cls,
                bind = self.bind)
        
        if self.on_proxytype: self.on_proxytype(proxytype)
        return proxytype

    def ext_proxytype(self, cls):
        if cls is object:
            breakpoint()

        proxytype = dynamic_proxytype(handler = self.ext_dispatch, cls = cls)
        proxytype.__retrace_source__ = 'external'

        if self.on_proxytype: self.on_proxytype(proxytype)
        
        return proxytype
    
    def function_target(self, obj): return obj

    def proxy_function(self, obj):
        return utils.wrapped_function(handler = self.ext_handler, target = obj)
    
    def proxy__new__(self, *args, **kwargs):
        return self.ext_handler(*args, **kwargs)

    def patchtype(self, cls):
        if not utils.is_extendable(cls):
            with WithFlags(cls, "Py_TPFLAGS_BASETYPE"):
                assert utils.is_extendable(cls)
                return self.patchtype(cls)

        if cls in self.immutable_types or issubclass(cls, tuple):
            return cls

        def wrap(func):
            return self.thread_state.dispatch(func, internal = self.proxy_function(func))

        def wrap_new(func):
            proxied = self.proxy_function(func)

            def new(cls, *args, **kwargs):
                instance = proxied(cls, *args, **kwargs)
                instance.__init__(*args, **kwargs)
                return instance
            
            return self.thread_state.dispatch(func, internal = new)

        # slots = {'__module__': cls.__module__, '__slots__': []}

        extended = utils.extend_type(cls)

        for name, value in superdict(cls).items():
            if callable(value) and not is_instance_method(value):
                setattr(extended, name, wrap_new(value) if name == '__new__' else wrap(value))

                # slots[name] = wrap_new(value) if name == '__new__' else wrap(value)
        extended.__module__ = cls.__module__

        return extended

    def is_entry_frame(self, frame):
        return frame.globals.get("__name__", None) == "__main__"

    def __call__(self, obj):
        assert not isinstance(obj, BaseException)
        assert not isinstance(obj, Proxy)
        assert not isinstance(obj, utils.wrapped_function)
            
        if type(obj) == type:
            return self.patchtype(obj)
            
        elif type(obj) in self.immutable_types:
            return obj
        
        elif is_function_type(type(obj)): 
            return self.thread_state.dispatch(obj, internal = self.proxy_function(obj))
        
        elif type(obj) == types.ClassMethodDescriptorType:
            func = self.thread_state.dispatch(obj, internal = self.proxy_function(obj))
            return classmethod(func)
        else:
            proxytype = dynamic_proxytype(handler = self.ext_dispatch, cls = type(obj))
            proxytype.__retrace_source__ = 'external'

            if self.on_proxytype: self.on_proxytype(proxytype)

            return utils.create_wrapped(proxytype, obj)
            # raise Exception(f'object {obj} was not proxied as its not a extensible type and is not callable')
