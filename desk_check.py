import sys
from collections import namedtuple
from pprint import pprint


# This documentation may be useful: https://docs.python.org/2/library/inspect.html
'''
TODO
Do not go inside functions that were not defined in the module
'''

src = open('example.py').read()
src_lines = src.split('\n')

stack = []
history = []
prev_line = None
prev_lineno = None

TraceData = namedtuple('TraceData', 'lineno,line,name_dicts,call_lineno')

def build_name_dicts(frame, *, name_dicts=None):
    f_name = frame.f_code.co_name
    f_name_tuple = (f_name,)
    if name_dicts:
        name_dicts = {f_name_tuple + k: v for k, v in name_dicts.items()}
    else:
        name_dicts = {}
    frame_dict = {}

    variables = frame.f_code.co_varnames + frame.f_code.co_names
    for v in variables:
        # We are only interested in simple variables, not functions (callable)
        if v in frame.f_locals and not callable(frame.f_locals[v]):
            frame_dict[v] = frame.f_locals[v]
    name_dicts[f_name_tuple] = frame_dict

    # The first level frame is this module, that shouldn't be included
    if frame.f_back and frame.f_back.f_back:
        return build_name_dicts(frame.f_back, name_dicts=name_dicts)
    return name_dicts


def is_def(f_name, cur_line):
    return cur_line and 'def ' in cur_line and f_name not in cur_line


def trace(frame, event, arg):
    global prev_line, prev_lineno
    f_name = frame.f_code.co_name
    lineno = frame.f_lineno
    try:
        cur_line = src_lines[lineno-1]
    except IndexError:
        cur_line = None
    if event == 'line':
        # print(cur_line)
        name_dicts = build_name_dicts(frame)
        # pprint(name_dicts)
        # print()
        if prev_line:
            history.append(TraceData(prev_lineno, prev_line, name_dicts, None))
        prev_line = cur_line
        prev_lineno = lineno
    elif event == 'call' and not is_def(f_name, cur_line):
        if prev_line:
            stack.append((prev_lineno, prev_line))
        # print('CALL', cur_line, event, arg)
        name_dicts = build_name_dicts(frame)
        # pprint(name_dicts)
        # print()
        if prev_line:
            history.append(TraceData(lineno, cur_line, name_dicts, prev_lineno))
        prev_line = None
        prev_lineno = None
    elif event == 'return':
        # print('RETURN', cur_line, event, arg)
        name_dicts = build_name_dicts(frame)
        # pprint(name_dicts)
        # print()
        if prev_line:
            history.append(TraceData(prev_lineno, prev_line, name_dicts, None))
        try:
            prev_lineno, prev_line = stack.pop()
        except IndexError:
            prev_lineno, prev_line = None, None

    return trace


sys.settrace(trace)

exec(src)

for h in history:
    print(h.line)
    pprint(h.name_dicts)
    print()
