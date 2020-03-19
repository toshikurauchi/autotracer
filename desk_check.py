import sys
from collections import namedtuple
import mock
from copy import deepcopy

# This documentation may be useful: https://docs.python.org/3/library/inspect.html
'''
TODO
Do not go inside functions that were not defined in the module
'''

TraceData = namedtuple('TraceData',
                       'line_i,line,name_dicts,call_line_i,retval,stdout')


class DeskChecker:
    def __init__(self):
        self._reset()
        self._check_function_name = self.check_str.__name__

    def _reset(self):
        self.stack = []
        self.history = []
        self.prev_line = None
        self.prev_lineno = None
        self.src = None
        self.src_lines = []
        self.mock_builtins = mock.MockBuiltins()

    def _build_name_dicts(self, frame, *, name_dicts=None, functions=None):
        if functions is None:
            functions = []
        f_name = frame.f_code.co_name
        if name_dicts:
            name_dicts = {
                '{0},{1}'.format(f_name, k): deepcopy(v)
                for k, v in name_dicts.items()
            }
        else:
            name_dicts = {}
        frame_dict = {}

        # TODO Maybe this is better: https://github.com/pgbovine/OnlinePythonTutor/blob/master/v5-unity/pg_logger.py#L431
        variables = frame.f_code.co_varnames + frame.f_code.co_names
        for v in variables:
            if v in frame.f_locals:
                value = frame.f_locals[v]
                if callable(value):
                    functions.append(value)
                else:
                    frame_dict[v] = deepcopy(value)
        name_dicts[f_name] = frame_dict

        # We should stop when we reach the frame that contains this object (and consequently _check_function_name)
        if frame.f_back and frame.f_back.f_code.co_name != self._check_function_name:
            return self._build_name_dicts(frame.f_back,
                                          name_dicts=name_dicts,
                                          functions=functions)
        return name_dicts, functions

    def _is_def(self, f_name, cur_line):
        return cur_line and 'def ' in cur_line and f_name not in cur_line

    def _trace(self, frame, event, arg):
        f_name = frame.f_code.co_name
        lineno = frame.f_lineno

        # Ignore other modules (change this if additional modules need to be traced)
        module_name = frame.f_globals.get('__name__')
        if module_name != '__main__':
            return self._trace

        try:
            call_line_i = self.stack[-1][0] - 1
        except IndexError:
            call_line_i = None
        try:
            cur_line = self.src_lines[lineno - 1]
        except IndexError:
            cur_line = None
        name_dicts, functions = self._build_name_dicts(frame)
        if event == 'line':
            if self.prev_line:
                self.history.append(
                    TraceData(self.prev_lineno - 1, self.prev_line, name_dicts,
                              call_line_i, None, self.mock_builtins.outputs))
            self.prev_line = cur_line
            self.prev_lineno = lineno
        elif event == 'call' and not self._is_def(f_name, cur_line):
            if self.prev_line:
                self.stack.append((self.prev_lineno, self.prev_line))
            if self.prev_line:
                if self.history:
                    last = self.history[-1]
                    self.history.append(
                        TraceData(self.prev_lineno - 1, self.prev_line,
                                  *last[2:]))
                self.history.append(
                    TraceData(lineno - 1, cur_line, name_dicts,
                              self.prev_lineno - 1, None,
                              self.mock_builtins.outputs))
            self.prev_line = None
            self.prev_lineno = None
        elif event == 'return':
            if self.prev_line:
                self.history.append(
                    TraceData(self.prev_lineno - 1, self.prev_line, name_dicts,
                              call_line_i, arg, self.mock_builtins.outputs))
            try:
                self.prev_lineno, self.prev_line = self.stack.pop()
            except IndexError:
                self.prev_lineno, self.prev_line = None, None

        return self._trace

    def check_file(self, filename):
        return self.check_str(open(filename).read())

    def check_str(self, src_str):
        self._reset()
        self.src = src_str
        self.src_lines = src_str.split('\n')

        with self.mock_builtins:
            sys.settrace(self._trace)
            exec(self.src, globals())
            sys.settrace(None)

        return self.history


if __name__ == "__main__":
    from pprint import pprint
    import json

    checker = DeskChecker()
    if len(sys.argv) < 2:
        history = checker.check_file('example.py')

        for h in history:
            print(h.line)
            pprint(h.name_dicts)
            print()
    else:
        history = checker.check_file(sys.argv[1])
        try:
            outfile = sys.argv[2]
            if not outfile.endswith('.json'):
                outfile += '.json'
        except IndexError:
            outfile = 'out.json'

        with open(outfile, 'w') as f:
            json.dump(history, f)
