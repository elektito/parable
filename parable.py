from cStringIO import StringIO

class ReadError(RuntimeError):
    pass

class EofReadError(ReadError):
    pass

class EvalError(RuntimeError):
    pass

class Symbol(object):
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return type(other) == Symbol and self.name == other.name

    def __ne__(self, other):
        return type(other) != Symbol or self.name != other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return '<Symbol "{}">'.format(self.name)

class Function(object):
    def __init__(self, params, body):
        if type(params) != list:
            raise EvalError('Invalid argument list; not a list.')

        if any(type(i) != Symbol for i in params):
            raise EvalError(
                'Function parameter list should only contain symbols.')

        self.params = params
        self.body = body

    def call(self, args, env):
        params = self.params

        if len(params) >= 2 and params[-2] == Symbol('&rest'):
            if len(args) < len(params) - 2:
                raise EvalError('Expected at least {} argument(s) but got {}.'
                                .format(len(params) - 2, len(args)))
        elif len(args) != len(params):
            raise EvalError('Expected {} argument(s) but got {}.'
                            .format(len(params), len(args)))

        if len(params) >= 2 and params[-2] == Symbol('&rest'):
            args = args[:len(params) - 2] + [args[len(params) - 2:]]
            params = params[:-2] + params[-1:]

        return eval(self.body, dict(env, **dict(zip(params, args))))

    def __repr__(self):
        return '<Function params={} body={}>'.format(self.params, self.body)

class Macro(object):
    def __init__(self, params, body):
        if type(params) != list:
            raise EvalError('Invalid argument list; not a list.')

        self.params = params
        self.body = body

    def expand(self, args, env):
        extra_env = destructure(self.params, args)
        return eval(self.body, dict(env, **extra_env))

    def __repr__(self):
        return '<Macro params={} body={}>'.format(self.params, self.body)

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

def macro_expand_1(exp, env):
    if type(exp) != list or len(exp) == 0:
        return exp, False

    try:
        macro = eval(exp[0], env)
    except EvalError:
        return exp, False

    if not isinstance(macro, Macro):
        return exp, False

    args = exp[1:]
    expanded = macro.expand(args, env)

    return expanded, True

def macro_expand(exp, env):
    result, is_expanded = macro_expand_1(exp, env)
    if not is_expanded:
        return result, False

    while is_expanded:
        result, is_expanded = macro_expand_1(result, env)

    return result, True

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

def eval_typeof(sexp, env):
    assert sexp[0].name == 'typeof'
    if len(sexp) != 2:
        raise EvalError('`typeof` form accepts exactly 1 argument; {} given.'.format(len(sexp) - 1))

    val = eval(sexp[1], env)
    val_type = {list: Symbol('list'),
                Symbol: Symbol('symbol'),
                Function: Symbol('function'),
                Macro: Symbol('macro'),
                int: Symbol('int'),
                str: Symbol('str')}.get(type(val), None)
    assert val_type != None
    return val_type

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
        raise EvalError('`rest` argument must be a list.')
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

def eval_apply(sexp, env):
    assert sexp[0].name == 'apply'
    if len(sexp) != 3:
        raise EvalError('`apply` expects 2 arguments; {} given.'.format(len(sexp) - 1))

    func = sexp[1]
    args = eval(sexp[2], env)
    return eval([func] + args, env)

def eval(exp, env):
    if type(exp) == list:
        return eval_sexp(exp, env)
    elif type(exp) == int:
        return exp
    elif type(exp) == str:
        return exp
    elif exp == Symbol('nil'):
        return []

    if exp not in env:
        raise EvalError('Undefined variable: {}'.format(exp.name))

    return env[exp]

def eval_sexp(sexp, env):
    if sexp == []:
        return []

    first = sexp[0]

    if first == Symbol('fn'):
        if len(sexp) != 3:
            raise EvalError('Invalid fn expression.')
        return Function(sexp[1], sexp[2])
    if first == Symbol('mac'):
        if len(sexp) != 3:
            raise EvalError('Invalid mac expression.')
        return Macro(sexp[1], sexp[2])

    map = {Symbol('if'): eval_if,
           Symbol('quote'): eval_quote,
           Symbol('prep'): eval_prep,
           Symbol('typeof'): eval_typeof,
           Symbol('first'): eval_first,
           Symbol('rest'): eval_rest,
           Symbol('eq'): eval_eq,
           Symbol('apply'): eval_apply}

    if type(first) == Symbol and first in map:
        return map[first](sexp, env)

    # it must be a function or macro call then.

    first = eval(sexp[0], env)
    if not isinstance(first, (Function, Macro)):
        raise EvalError('Not a function or a macro: {}'.format(first))

    args = sexp[1:]

    if isinstance(first, Function):
        # evaluate arguments.
        args = [eval(i, env) for i in args]

        return first.call(args, env)
    elif isinstance(first, Macro):
        # now expand the macro.
        expanded = first.expand(args, env)

        # evaluate the result of expansion.
        return eval(expanded, env)
    else:
        raise EvalError('Expected a macro or a function, got: {}'
                        .format(first))

def skip_whitespace(f):
    b = f.read(1)
    while b:
        if b not in '; \t\r\n':
            f.seek(-1, 1)
            break

        if b == ';':
            while b and b != '\n':
                b = f.read(1)

        b = f.read(1)

def read_item(f):
    skip_whitespace(f)
    item = ''
    b = f.read(1)
    if b == "'":
        return [Symbol('quote'), read(f)]

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
        skip_whitespace(f)
        b = f.read(1)

        if not b:
            raise EofReadError('Unexpected end of file.')

        if b == ')':
            return items

        f.seek(-1, 1)
        if b == '(':
            items.append(read_list(f))
        else:
            items.append(read_item(f))

def read(f):
    skip_whitespace(f)
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
