import retracesoftware.functional as functional
import retracesoftware_utils as utils
import retracesoftware.stream as stream

from retracesoftware.install.tracer import Tracer
from retracesoftware.proxy.thread import per_thread_messages, thread_id
from retracesoftware.proxy.proxytype import *
# from retracesoftware.proxy.gateway import gateway_pair
from retracesoftware.proxy.record import StubRef, Placeholder
from retracesoftware.proxy.proxysystem import ProxySystem, RetraceError
from retracesoftware.proxy.stubfactory import StubFactory, Stub, StubFunction
from retracesoftware.proxy.globalref import GlobalRef

import os
import weakref
import traceback
import pprint

from itertools import count, islice

# we can have a dummy method descriptor, its has a __name__ and when called, returns the next element

# for types, we can patch the __new__ method
# do it from C and immutable types can be patched too
# patch the tp_new pointer?

class ReplayError(RetraceError):
    pass

def count_matching(*lists):
    count = 0
    for slice in zip(*lists):
        if len(set(slice)) == 1:
            count += 1
        else:
            break

    return count

def on_stack_mismatch(last_matching, record, replay):
    # print('Common:')
    # for index, common, replay, record in zip(count(), last_matching_stack, args[0], record):
    #     if common == replay == record:
    #         print(common)
    if last_matching:
        matching = count_matching(reversed(last_matching),
                                reversed(record),
                                reversed(replay))

        print('Common stacktrace:')
        for line in reversed(list(islice(reversed(last_matching), matching))):
            print(line)
        
        print('last matching stacktrace:')
        for line in islice(last_matching, 0, len(last_matching) - matching):
            print(line)

        print('Replay stacktrace:')
        for line in islice(replay, 0, len(replay) - matching):
            print(line)

        print('Record stacktrace:')
        for line in islice(record, 0, len(record) - matching):
            print(line)
        
        print(f'-----------')
    else:
        matching = count_matching(reversed(record), reversed(replay))

        print('Common stacktrace:')
        for line in reversed(list(islice(reversed(record), matching))):
            print(line)
        
        print('Replay stacktrace:')
        for line in islice(replay, 0, len(replay) - matching):
            print(line)

        print('Record stacktrace:')
        for line in islice(record, 0, len(record) - matching):
            print(line)
        


class ReplayProxySystem(ProxySystem):
    
    @utils.striptraceback
    def next_result(self):
        try:
            while True:
                next = self.messages()

                if next == 'CALL':
                    func = self.messages()
                    args = self.messages()
                    kwargs = self.messages()

                    try:
                        func(*args, **kwargs)
                    except:
                        pass

                elif next == 'RESULT':
                    return self.messages()
                
                elif next == 'ERROR':
                    # breakpoint()
                    err_type = self.messages()
                    err_value = self.messages()
                    utils.raise_exception(err_type, err_value)
                else:
                    assert type(next) is not str
                    return next
        except TimeoutError:
            print(f'timeout for reader, active thread: {self.reader.active_thread}, next_control: {self.reader.next_control}')

            for thread,stack in self.reader.stacktraces.items():
                print(f'thread: {thread}')

                formatted_frames = [
                    (frame.filename, frame.lineno, frame.function, frame.code_context[0].strip() if frame.code_context else None)
                    for frame in stack
                ]
                formatted_trace = traceback.format_list(formatted_frames)
                print("Traceback (most recent call last):\n" + "".join(formatted_trace))

            utils.sigtrap(None)

    def bind(self, obj):
        read = self.messages()
        
        assert isinstance(read, Placeholder)

        self.bindings[read] = obj

    # def dynamic_path(self):
    #     if self.getpid() != self.pid:
    #         self.pid = self.getpid()
    #         # ok we are in child, calculate new path
    #         self.path = self.path / f'fork-{self.fork_counter}'
    #         self.fork_counter = 0
        
    #     return self.path

    def after_fork_in_child(self):
        self.reader.path = self.new_child_path(self.reader.path)
        super().after_fork_in_child()

    # def dynamic_ext_proxytype(self, cls):
    #     raise Exception('dynamic_ext_proxytype should not be called in replay')

    def proxy_function(self, obj):
        func = functional.repeatedly(self.next_result)
        func.__name__ = obj.__name__

        return super().proxy_function(func)

    def proxy__new__(self, __new__, *args, **kwargs):
        func = functional.repeatedly(self.next_result)
        func.__name__ = '__new__'
        return super().proxy__new__(func, *args, **kwargs)

    def basetype(self, cls):
        return self.stub_factory.create_stubtype(StubRef(cls))

    def readnext(self):
        with self.thread_state.select('disabled'):
            try:
                # obj = self.messages()
                # print(f'read: {obj}')
                # return obj
                return self.messages()
            except Exception as error:
                # print(f'Error reading stream: {error}')
                traceback.print_exc()
                os._exit(1)

    def read_required(self, required):
        obj = self.readnext()
        if obj != required:
            print('---------------------------------')
            print('last matching stack')
            print('---------------------------------')
            if self.last_matching_stack:
                for line in self.last_matching_stack:
                    print(line)

            print('---------------------------------')
            print(f'Replay: {required}')
            print('---------------------------------')
            for line in utils.stacktrace():
                print(line)
            print('---------------------------------')
            print(f'Record: {obj}')
            print('---------------------------------')
            for i in range(15):
                print(self.readnext())

            breakpoint()
            os._exit(1)
            raise Exception(f'Expected: {required} but got: {obj}')
        
        # self.last_matching_stack = utils.stacktrace()

    def trace_writer(self, name, *args):
        with self.thread_state.select('disabled'):
            # read = self.messages_read

            self.read_required('TRACE')
            # self.read_required(read)
            self.read_required(name)

            if name == 'stacktrace':
                print('FOOO!!!')
                os._exit(1)
                record = self.readnext()
                if args[0] == record:
                    self.last_matching_stack = args[0]
                else:
                    on_stack_mismatch(
                        last_matching = self.last_matching_stack,
                        record = record,
                        replay = args[0])                        
                    os._exit(1)
            else:
                # print(f'Trace: {self.reader.messages_read} {name} {args}')
                for arg in args:
                    self.read_required(arg)

    def on_thread_exit(self, thread_id):
        print(f'on_thread_exit!!!!')
        self.reader.wake_pending()

    def is_entry_frame(self, frame):
        if super().is_entry_frame(frame) and frame.function.__code__.co_filename == self.mainscript:
            return True
        return False

    def __init__(self, 
                 thread_state,
                 immutable_types,
                 tracing_config,
                 mainscript,
                 path,
                 fork_path = []):
        
        # self.messages_read = 0

        self.mainscript = mainscript

        self.reader = stream.reader(path, 
                                    thread = thread_id,
                                    timeout_seconds = 60)
    
        self.bindings = utils.id_dict()
        # self.set_thread_id = utils.set_thread_id
        self.fork_path = fork_path
        deserialize = functional.walker(self.bindings.get_else_key)

        # def count(res):
        #     self.messages_read += 1
        #     return res

        read_res = functional.vector(functional.lazy(getattr, self.reader, 'messages_read'), self.reader)

        def foo():
            try:
                messages_read, res = read_res()
                if issubclass(type(res), Stub):
                    print(f'res: {utils.thread_id()} {messages_read} stub: {type(res)}')
                else:
                    print(f'res: {utils.thread_id()} {messages_read} {res}')

                return res
            except Exception as error:
                print(f'Error reading next result: {error}')
                raise(error)
        
        # self.messages = functional.sequence(per_thread_messages(foo), deserialize)

        self.messages = functional.sequence(self.reader, deserialize)

        self.stub_factory = StubFactory(thread_state = thread_state, next_result = self.next_result)

        self.last_matching_stack = None

        self.reader.type_deserializer[StubRef] = self.stub_factory
        self.reader.type_deserializer[GlobalRef] = lambda ref: ref()
                
        read_sync = thread_state.dispatch(utils.noop, internal = functional.lazy(thread_state.wrap('disabled', self.read_required), 'SYNC'))

        self.sync = lambda function: utils.observer(on_call = read_sync, function = function)

        super().__init__(thread_state = thread_state, 
                         tracer = Tracer(tracing_config, writer = self.trace_writer),
                         immutable_types = immutable_types)
