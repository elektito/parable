from parable import Symbol, eval as eval_form, EvalError, macro_expand, List
from read import Reader, ReadError, EofReadError

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

if __name__ == '__main__':
    from sys import argv
    if len(argv) < 2:
        print
        print 'usage: {} [files] form'.format(argv[0])
        print
        exit(10)

    files = [] if len(argv) == 2 else argv[1:-1]

    env = {}
    for filename in files:
        with open(filename) as f:
            try:
                env.update(load(f, filename, env))
            except LoadWarning as w:
                print 'Warning in file {}:'.format(filename), w
                if w.form != None:
                    print '   form:', w.form
                exit(11)
            except LoadError as e:
                print 'Error in file {}:'.format(filename), e
                if e.form != None:
                    print '   form:', e.form
                exit(11)
            except ReadError as e:
                print 'Read Error in file {}:'.format(filename), e
                exit(11)
            except EvalError as e:
                print 'Eval Error in file {}:'.format(filename), e
                print_error(e)
                exit(11)

    try:
        ret = eval_form(Reader(argv[-1], '<string>').read(), env)
    except ReadError as e:
        print 'Read Error:', e
    except EvalError as e:
        print 'Eval Error:', e
        print_error(e)
    else:
        print ret
