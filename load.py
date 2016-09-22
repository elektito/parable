#!/usr/bin/env python

from parable import Symbol, eval as eval_form, macro_expand, List, Error
from read import Reader, ReadError, EofReadError
from pprint import pprint
from util import InvalidAssocList, assoc

class LoadWarning(RuntimeWarning):
    def __init__(self, msg, form):
        super(LoadWarning, self).__init__(msg)
        self.form = form

class LoadError(RuntimeError):
    def __init__(self, msg, form):
        super(LoadError, self).__init__(msg)
        self.form = form

def display_form(form, context):
    if form.filename == '<string>':
        return

    with open(form.filename) as f:
        all_lines = f.readlines()

    lines = zip(xrange(form.start_row, form.end_row + 1),
                all_lines[form.start_row:form.end_row + 1])

    if not context:
        pass
    elif form.start_row == 1:
        lines = [(0, all_lines[0])] + lines
    elif form.start_row > 1:
        lines = [(form.start_row - 2, all_lines[form.start_row - 2]),
                 (form.start_row - 1, all_lines[form.start_row - 1])] + lines

    if not context:
        pass
    elif form.end_row == len(all_lines) - 2:
        lines.append((len(all_lines) - 1, all_lines[-1]))
    elif form.end_row < len(all_lines) - 2:
        lines.extend([(form.end_row + 1, all_lines[form.end_row + 1]),
                      (form.end_row + 2, all_lines[form.end_row + 2])])

    d = dict(
        LINE_NO_COLOR = '\033[95m',
        CODE_COLOR = '\033[92m',
        HIGHLIGHT_COLOR = '\033[93m',
        END_COLOR = '\033[0m')

    for lineno, line in lines:
        line = line[:-1] if line.endswith('\n') else line
        if lineno < form.start_row or lineno > form.end_row:
            first_part = line
            second_part = third_part = ''
        elif form.start_row == lineno and form.end_row != lineno:
            first_part=line[:form.start_col]
            second_part=line[form.start_col:]
            third_part=''
        elif form.end_row == lineno and form.start_row != lineno:
            first_part=''
            second_part=line[:form.end_col+1]
            third_part=line[form.end_col+1:]
        elif form.start_row < lineno < form.end_row:
            first_part = ''
            second_part = line
            third_part = ''
        else:
            first_part=line[:form.start_col]
            second_part=line[form.start_col:form.end_col+1]
            third_part=line[form.end_col+1:]

        d2 = dict(lineno=lineno,
                  first_part=first_part,
                  second_part=second_part,
                  third_part=third_part)
        print '{LINE_NO_COLOR}{lineno}:\t' \
            '{CODE_COLOR}{first_part}{HIGHLIGHT_COLOR}' \
            '{second_part}{CODE_COLOR}{third_part}{END_COLOR}'.format(**dict(d, **d2))

def print_exception(e):
    if not hasattr(e, 'form') or \
       not all(hasattr(e.form, a) for a in ['start_row',
                                            'start_col',
                                            'end_row',
                                            'end_col',
                                            'filename']) or \
       e.form.filename.startswith('<') or e.form.filename == '':
        print e
        return

    print 'Error:', e

    display_form(e.form, True)

def print_error(e):
    try:
        msg = assoc(e.attrs, Symbol(':msg'))
    except (KeyError, InvalidAssocList):
        msg = ''

    try:
        form = assoc(e.attrs, Symbol(':form'))
    except (KeyError, InvalidAssocList):
        form = e

    if msg:
        print 'Error of type "{}": {}'.format(e.type.name, msg)
    else:
        print 'Error of type "{}".'.format(e.type.name)

    if form:
        display_form(form, True)

def run_tests(f, filename, env):
    passed = 0
    failed = 0
    error = 0

    reader = Reader(f, filename)
    while True:
        form = reader.read()

        if form == None:
            break

        result = eval_form(form, env)
        if result == False:
            failed += 1
            print 'Test failed:'
            display_form(form, False)
        elif result == True:
            passed += 1
            print 'Test passed.'
        elif isinstance(result, Error):
            error += 1

            try:
                desc = assoc(result.attrs, Symbol(':msg'))
                print 'Test error ({}): {}'.format(result.type.name, desc)
            except (KeyError, InvalidAssocList) as e:
                print 'Test error ({}).'.format(result.type.name)

            try:
                form = assoc(result, Symbol(':form'))
                display_form(form, False)
            except (KeyError, InvalidAssocList):
                print 'No location information for the error.'
        else:
            error += 1
            print 'Test cases must return either #t or #f; got {}.'.format(result)
            display_form(form, False)

    return passed, failed, error

def load(f, filename, env):
    reader = Reader(f, filename)
    while True:
        form = reader.read()

        if form == None:
            break

        expanded, _ = macro_expand(form, env)

        if type(expanded) != List or len(expanded) != 3 or expanded[0] != Symbol('define'):
            raise LoadWarning('Unrecognized top-level form.', expanded)

        if type(expanded[1]) != Symbol:
            raise LoadError('Invalid top-level form.', form)

        val = eval_form(expanded[2], env)
        if isinstance(val, Error):
            print_error(val)
            exit(2)
        env[expanded[1]] = val

    return env

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Loads and evaluates parable files and expressions.')
    parser.add_argument('-l', '--load', type=str, dest='load_files',
                        nargs='+', metavar='FILES',
                        help='Load one or more files.')
    parser.add_argument('-t', '--test', type=str, dest='test_files',
                        nargs='+', metavar='FILES',
                        help='run one or more test files.')
    parser.add_argument('-e', '--eval', type=str, dest='eval_expression',
                        metavar='EXPR',
                        help='Evaluate the given expression.')
    parser.add_argument('-m', '--macro-expand', type=str,
                        dest='expand_expression', metavar='EXPR',
                        help='Macro-expand the given expression.')
    args = parser.parse_args()

    count = len(list(
        1 for i in ('eval_expression',
                    'expand_expression',
                    'test_files')
        if getattr(args, i) != None))

    if count > 1:
        print 'Only one of -t, -m and -e can be used.'
        exit(1)
    elif count == 0:
        print 'Either -t, -m or -e must be used.'
        exit(1)

    env = {}
    for lib in args.load_files:
        with open(lib) as f:
            try:
                env.update(load(f, lib, env))
            except (LoadError, LoadWarning) as e:
                print_exception(e)
                exit(2)

    if args.eval_expression:
        try:
            form = Reader(args.eval_expression, '<string>').read()
            result = eval_form(form, env)
        except ReadError as e:
            print_exception(e)
            exit(2)
        if isinstance(result, Error):
            print_error(result)
            exit(2)
        print 'Evaluation Result:', pprint(result)
    elif args.expand_expression:
        try:
            form = Reader(args.expand_expression, '<string>').read()
            result = macro_expand(form, env)
        except ReadError as e:
            print_exception(e)
            exit(2)
        if isinstance(result, Error):
            print_error(result)
            exit(2)
        print 'Macro Expansion Result:', result[1], pprint(result[0])
    elif args.test_files:
        passed = failed = error = 0
        for test_file in args.test_files:
            try:
                with open(test_file) as f:
                    p, f, e = run_tests(f, test_file, env)
                    passed += p
                    failed += f
                    error += e
            except ReadError as e:
                print_exception(e)
                exit(2)

        print 'Total tests:', passed + failed + error
        print '   Successful:', passed
        print '   Failed:', failed
        print '   Error:', error

        if failed != 0 or error != 0:
            exit(3)

if __name__ == '__main__':
    main()
