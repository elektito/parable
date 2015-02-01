from cStringIO import StringIO

class ReadError(RuntimeError):
    pass

class EvalError(RuntimeError):
    pass

class Symbol(object):
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return type(other) == Symbol and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return '<Symbol "{}">'.format(self.name)

def destructure(params, args):
    if type(params) == list and type(args) != list:
        raise EvalError('Parameter list and the provided arguments do not match.\n'
                        '    Expected a list in the arguments, got: {}'
                        .format(args))

    if len(params) >= 2 and params[-2] == Symbol('&rest'):
        if len(args) < len(params) - 2:
            raise EvalError('Parameter list and the provided arguments do not match.\n'
                            '    Expected at least {} argument(s) but got {}.'
                            .format(len(params) - 2, len(args)))

        args = args[:len(params) - 2] + [args[len(params) - 2:]]
        del params[-2]
    elif len(params) != len(args):
        raise EvalError('Parameter list and the provided arguments do not match.\n'
                        '    Expected {} argument(s) but got {}.'
                        .format(len(params), len(args)))

    env = {}
    for p, a in zip(params, args):
        if type(p) == Symbol:
            env[p] = a
        elif type(p) == list:
            env.update(destructure(p, a))
        else:
            raise EvalError('Only symbols and lists allowed in parameter list; got a', type(p))

    return env

def eval_if(sexp, env):
    assert sexp[0].name == 'if'
    if len(sexp) != 4:
        raise EvalError('`if` form accepts exactly 3 arguments; {} given.'.format(len(sexp) - 1))

    cond = eval(sexp[1], env)
    if cond == []:
        return eval(sexp[3], env)
    else:
        return eval(sexp[2], env)

def eval_quote(sexp, env):
    assert sexp[0].name == 'quote'
    if len(sexp) != 2:
        raise EvalError('`if` form accepts exactly 1 argument; {} given.'.format(len(sexp) - 1))
    return sexp[1]

def eval_atom(sexp, env):
    assert sexp[0].name == 'atom'
    if len(sexp) != 2:
        raise EvalError('`atom` form accepts exactly 1 argument; {} given.'.format(len(sexp) - 1))

    val = eval(sexp[1], env)
    if type(val) == list:
        return []
    else:
        return Symbol('t')

def eval_first(sexp, env):
    assert sexp[0].name == 'first'
    if len(sexp) != 2:
        raise EvalError('`first` form accepts exactly 1 argument; {} given.'.format(len(sexp) - 1))
    ret = eval(sexp[1], env)
    if type(ret) != list:
        raise EvalError('`first` argument must be a list.')
    return ret[0]

def eval_rest(sexp, env):
    assert sexp[0].name == 'rest'
    if len(sexp) != 2:
        raise EvalError('`rest` form accepts exactly 1 argument; {} given.'.format(len(sexp) - 1))
    ret = eval(sexp[1], env)
    if type(ret) != list:
        raise EvalError('`rerst` argument must be a list.')
    return ret[1:]

def eval_prep(sexp, env):
    assert sexp[0].name == 'prep'
    if len(sexp) != 3:
        raise EvalError('`prep` form accepts exactly 2 argument; {} given.'.format(len(sexp) - 1))
    first = eval(sexp[1], env)
    rest = eval(sexp[2], env)
    if type(rest) != list:
        raise EvalError('`prep` second argument must be a list.')
    return [first] + rest

def eval_eq(sexp, env):
    assert sexp[0].name == 'eq'
    if len(sexp) != 3:
        raise EvalError('`first` form accepts exactly 2 argument; {} given.'.format(len(sexp) - 1))
    first = eval(sexp[1], env)
    second = eval(sexp[2], env)
    if type(first) != list and type(second) != list:
        return Symbol('t') if first == second else []
    else:
        return []

def eval(exp, env):
    if type(exp) == list:
        return eval_sexp(exp, env)
    elif type(exp) == int:
        return exp
    elif type(exp) == str:
        return exp

    if exp not in env:
        raise EvalError('Undefined variable: {}'.format(exp.name))

    return env[exp]

def eval_sexp(sexp, env):
    if sexp == []:
        return []

    first = sexp[0]

    if first in (Symbol('fn'), Symbol('mac')):
        if len(sexp) != 3:
            raise EvalError('Invalid fn/mac expression.')
        return sexp

    map = {Symbol('if'): eval_if,
           Symbol('quote'): eval_quote,
           Symbol('prep'): eval_prep,
           Symbol('atom'): eval_atom,
           Symbol('first'): eval_first,
           Symbol('rest'): eval_rest,
           Symbol('eq'): eval_eq}

    if type(first) == Symbol and first in map:
        return map[first](sexp, env)

    # it must be a function or macro call then.

    first = eval(sexp[0], env)
    if type(first) != list:
        raise EvalError('Expected to find an fn or mac expression.')
    if type(first[1]) != list:
        raise EvalError('Invalid argument list; not a list.')

    params = first[1]
    body = first[2]
    args = sexp[1:]

    if len(params) >= 2 and params[-2] == Symbol('&rest'):
        if len(args) < len(params) - 2:
            raise EvalError('Expected at least {} argument(s) but got {}.'
                            .format(len(params) - 2, len(args)))
    elif len(args) != len(params):
        raise EvalError('Expected {} argument(s) but got {}.'
                        .format(len(params), len(args)))

    if first[0] == Symbol('fn'):
        if any(type(i) != Symbol for i in params):
            raise EvalError(
                'Function parameter list should only contain symbols.')

        # evaluate arguments.
        args = [eval(i, env) for i in args]

        if params[-2] == Symbol('&rest'):
            args = args[:len(params) - 2] + [args[len(params) - 2:]]
            del params[-2]

        return eval(body, dict(env, **dict(zip(params, args))))
    elif first[0] == Symbol('mac'):
        # macro arguments can be destructuring.
        extra_env = destructure(params, args)

        # now expand the macro.
        expanded = eval(body, dict(env, **extra_env))

        # evaluate the result of expansion.
        return eval(expanded, env)
    else:
        raise EvalError('Expected a macro or a function, got: {}'
                        .format(first))

def read_item(f):
    item = ''
    b = f.read(1)
    if b == "'":
        return [Symbol('quote'), read(f)]

    if b == ';':
        while b and b != '\n':
            b = f.read(1)
        b = f.read(1)

        if b == '(':
            f.seek(-1, 1)
            return read_list(f)
        elif b == '':
            return None

    while b and b not in '() \'\n\t\r;':
        item += b
        b = f.read(1)

    if b:
        f.seek(-1, 1)

    try:
        # is this an integer?
        integer = int(item)

        # yes, it is.
        return integer
    except:
        pass # not an integer

    # is it a string literal?
    if len(item) >= 2 and item[0] == '"' and item[-1] == '"':
        return item[1:-1]

    return Symbol(item)

def read_list(f):
    b = f.read(1)
    if not b or b != '(':
        raise ReadError('Expected "(".')

    items = []

    while True:
        b = f.read(1)

        if b == ';':
            while b and b != '\n':
                b = f.read(1)
            b = f.read(1)

        while b and b in ' \t\r\n':
            b = f.read(1)
        if not b:
            raise ReadError('Unexpected end of file.')

        if b == ')':
            return items

        f.seek(-1, 1)
        if b == '(':
            items.append(read_list(f))
        else:
            items.append(read_item(f))

def read(f):
    b = f.read(1)
    while b and b in ' \t\n\r':
        b = f.read(1)
    if not b:
        return None

    f.seek(-1, 1)
    if b == '(':
        return read_list(f)
    else:
        return read_item(f)

def read_str(s):
    return read(StringIO(s))
