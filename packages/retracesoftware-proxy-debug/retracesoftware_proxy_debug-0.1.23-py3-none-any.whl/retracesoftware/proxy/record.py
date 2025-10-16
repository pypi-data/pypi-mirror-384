import retracesoftware.functional as functional
import retracesoftware.utils as utils
import retracesoftware.stream as stream

from retracesoftware.proxy.proxytype import *
# from retracesoftware.proxy.gateway import gateway_pair
from retracesoftware.proxy.proxysystem import ProxySystem
from retracesoftware.proxy.thread import write_thread_switch, ThreadSwitch, thread_id
from retracesoftware.install.tracer import Tracer
from retracesoftware.proxy.stubfactory import StubRef, ExtendedRef
from retracesoftware.proxy.globalref import GlobalRef

import sys
import os
import types
import gc

class Placeholder:
    __slots__ = ['id', '__weakref__']

    def __init__(self, id):
        self.id = id
    
def keys_where_value(pred, dict):
    for key,value in dict.items():
        if pred(value): yield key

types_lookup = {v:k for k,v in types.__dict__.items() if isinstance(v, type)}

def resolve(obj):
    try:
        return getattr(sys.modules[obj.__module__], obj.__name__)
    except:
        return None
    
def resolveable(obj):
    try:
        return getattr(sys.modules[obj.__module__], obj.__name__) is obj
    except:
        return False

def resolveable_name(obj):
    if obj in types_lookup:
        return ('types', types_lookup[obj])
    elif resolve(obj) is obj:
        return (obj.__module__, obj.__name__)
    else:
        return None

# when 
class RecordProxySystem(ProxySystem):
    
    def bind(self, obj):
        self.bindings[obj] = self.writer.handle(Placeholder(self.next_placeholder_id))
        self.writer(self.bindings[obj])
        self.next_placeholder_id += 1

    def before_fork(self):
        self.writer.close()
        super().before_fork()
        # self.writer.path = self.dynamic_path

    def after_fork_in_child(self):
        new_path = self.new_child_path(self.writer.path)
        new_path.parent.mkdir()
        self.writer.path = new_path
        super().after_fork_in_child()

    def after_fork_in_parent(self):
        super().after_fork_in_parent()
        self.thread_state.value = self.saved_thread_state
        self.writer.reopen()
    
    def set_thread_id(self, id):
        utils.set_thread_id(self.writer.handle(ThreadSwitch(id)))
        # utils.set_thread_id(id)

    def is_entry_frame(self, frame):
        if super().is_entry_frame(frame):
            self.write_main_path(frame.function.__code__.co_filename)
            return True
        return False

    def __init__(self, thread_state, 
                 immutable_types, 
                 tracing_config,
                 write_main_path,
                 path):
        
        self.fork_counter = 0
        self.write_main_path = write_main_path

        self.getpid = thread_state.wrap(
            desired_state = 'disabled', function = os.getpid)
        
        self.pid = self.getpid()

        self.writer = stream.writer(path = path, thread = thread_id)
        
        # def on_switch():
        #     print(f"On thread switch!!!")
        #     # print(f"On thread switch!!!: {utils.thread_id().id}")
        #     # utils.sigtrap(utils.thread_id())
        #     self.writer(utils.thread_id())
        #     # utils.sigtrap(utils.thread_id())

        # write = utils.observer(on_call = utils.thread_switch_monitor(on_switch), function = self.writer)

        # w = self.writer.handle('TRACE')
        # def trace_writer(*args):
        #     print(f'Trace: {args}')
        #     w(*args)

        self.extended_types = {}
        self.bindings = utils.id_dict()
        self.next_placeholder_id = 0

        serialize = functional.walker(self.bindings.get_else_key)
        
        # def on_switch():
        #     print("On thread switch!!!")
        #     # utils.sigtrap(utils.thread_id())
        #     utils.thread_id()()
        #     # utils.sigtrap(utils.thread_id())

        # self.thread_switch_monitor = utils.thread_switch_monitor(on_switch)

        # self.thread_switch_monitor = utils.thread_switch_monitor(functional.repeatedly(utils.thread_id))

        # self.sync = lambda function: functional.firstof(self.thread_switch_monitor, functional.always(self.writer.handle('SYNC')), function)

        sync_handle = self.writer.handle('SYNC')

        write_sync = thread_state.dispatch(utils.noop, internal = functional.lazy(sync_handle))

        self.sync = lambda function: \
            utils.observer(on_call = write_sync, function = function)

        error = self.writer.handle('ERROR')

        def write_error(cls, val, traceback):
            error(cls, val)
        
        # self.set_thread_id = functional.partial(utils.set_thread_id, self.writer)

        # w = self.writer.handle('TRACE')
        # def foo(name, *args):
        #     print(f'writing: {self.writer.messages_written} {name} {args}')
        #     w(self.writer.messages_written, name, *args)

        # tracer = Tracer(tracing_config, writer = foo)
        tracer = Tracer(tracing_config, writer = self.writer.handle('TRACE'))

        # self.wrap_int_to_ext = self.sync
        
        self.on_int_call = functional.mapargs(transform = serialize, function = self.writer.handle('CALL'))
        
        self.on_ext_result = functional.sequence(serialize, self.writer.handle('RESULT'))
        
        self.on_ext_error = write_error

        self.ext_apply = self.int_apply = functional.apply

        self.writer.type_serializer[types.ModuleType] = GlobalRef

        super().__init__(thread_state = thread_state, 
                         tracer = tracer, 
                         immutable_types = immutable_types)

    def ext_proxytype(self, cls):
        
        proxytype = super().ext_proxytype(cls)

        ref = self.writer.handle(StubRef(proxytype))
  
        self.writer.type_serializer[proxytype] = functional.constantly(ref)

        return proxytype
