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
                exit(11)

    try:
        ret = eval_form(Reader(argv[-1], '<string>').read(), env)
    except ReadError as e:
        print 'Read Error:', e
    except EvalError as e:
        print 'Eval Error:', e
        print e.form
        print e.form.start_row, e.form.start_col, e.form.end_row, e.form.end_col
    else:
        print ret
