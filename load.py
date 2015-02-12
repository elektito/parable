from parable import Symbol, eval as eval_form, EvalError, macro_expand, List
from read import Reader, ReadError, EofReadError
from pprint import pprint

class LoadWarning(RuntimeWarning):
    def __init__(self, msg, form):
        super(LoadWarning, self).__init__(msg)
        self.form = form

class LoadError(RuntimeError):
    def __init__(self, msg, form):
        super(LoadError, self).__init__(msg)
        self.form = form

def print_error(e):
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

    with open(e.form.filename) as f:
        all_lines = f.readlines()

    lines = zip(xrange(e.form.start_row, e.form.end_row + 1),
                all_lines[e.form.start_row:e.form.end_row + 1])

    if e.form.start_row == 1:
        lines = [(0, all_lines[0])] + lines
    elif e.form.start_row > 1:
        lines = [(e.form.start_row - 2, all_lines[e.form.start_row - 2]),
                 (e.form.start_row - 1, all_lines[e.form.start_row - 1])] + lines

    if e.form.end_row == len(all_lines) - 2:
        lines.append((len(all_lines - 2), all_lines[-2]))
    elif e.form.end_row < len(all_lines) - 2:
        lines.extend([(e.form.end_row + 1, all_lines[e.form.end_row + 1]),
                      (e.form.end_row + 2, all_lines[e.form.end_row + 2])])

    d = dict(
        LINE_NO_COLOR = '\033[95m',
        CODE_COLOR = '\033[92m',
        HIGHLIGHT_COLOR = '\033[93m',
        END_COLOR = '\033[0m')

    for lineno, line in lines:
        line = line[:-1] if line.endswith('\n') else line
        if lineno < e.form.start_row or lineno > e.form.end_row:
            first_part = line
            second_part = third_part = ''
        elif e.form.start_row == lineno and e.form.end_row != lineno:
            first_part=line[:e.form.start_col]
            second_part=line[e.form.start_col:]
            third_part=''
        elif e.form.end_row == lineno and e.form.start_row != lineno:
            first_part=''
            second_part=line[:e.form.end_col+1]
            third_part=line[e.form.end_col+1:]
        else:
            first_part=line[:e.form.start_col]
            second_part=line[e.form.start_col:e.form.end_col+1]
            third_part=line[e.form.end_col+1:]

        d2 = dict(lineno=lineno,
                  first_part=first_part,
                  second_part=second_part,
                  third_part=third_part)
        print '{LINE_NO_COLOR}{lineno}: ' \
            '{CODE_COLOR}{first_part}{HIGHLIGHT_COLOR}' \
            '{second_part}{CODE_COLOR}{third_part}{END_COLOR}'.format(**dict(d, **d2))

def run_tests(f, filename, env):
    passed = 0
    failed = 0
    error = 0

    reader = Reader(f, filename)
    while True:
        form = reader.read()

        if form == None:
            break

        try:
            result = eval_form(form, env)
            if result == []:
                failed += 1
                print 'Test failed.'
            elif result == Symbol('t'):
                passed += 1
                print 'Test passed.'
            else:
                error += 1
                print 'Test cases must return either t or nil; got {}.'.format(result)
        except EvalError as e:
            print 'Test error:', e
            error += 1

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

        env[expanded[1]] = eval_form(expanded[2], env)

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
                print_error(e)
                exit(2)

    if args.eval_expression:
        try:
            form = Reader(args.eval_expression, '<string>').read()
            result = eval_form(form, env)
        except (ReadError, EvalError) as e:
            print_error(e)
            exit(2)
        print 'Evaluation Result:', pprint(result)
    elif args.expand_expression:
        try:
            form = Reader(args.expand_expression, '<string>').read()
            result = macro_expand(form, env)
        except (ReadError, EvalError) as e:
            print_error(e)
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
                print_error(e)
                exit(2)

        print 'Total tests:', passed + failed + error
        print '   Successful:', passed
        print '   Failed:', failed
        print '   Error:', error

        if failed != 0 or error != 0:
            exit(3)

if __name__ == '__main__':
    main()
