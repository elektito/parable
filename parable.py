from cStringIO import StringIO
from util import assoc

class ParamError(RuntimeError):
    def __init__(self, msg, form):
        self.form = form
        super(ParamError, self).__init__(msg)

class ArgError(RuntimeError):
    def __init__(self, msg, form):
        self.form = form
        super(ArgError, self).__init__(msg)

class Error(object):
    def __init__(self, type, attrs):
        self.type = type
        self.attrs = attrs

        self.start_row = 0
        self.start_col = 0
        self.end_row = 0
        self.end_col = 0
        self.filename = ''

    def __eq__(self, other):
        if type(other) != Error:
            return False
        return self.type == other.type

    def __repr__(self):
        return '<Error "{}" attrs={}>'.format(self.type.name, self.attrs)

def create_error(typestr, *attrs):
    def process_attrs(attrs, acc):
        if attrs == ():
            return Error(Symbol(typestr), List(acc))
        elif len(attrs) >= 2:
            acc.append(Symbol(attrs[0]))
            acc.append(attrs[1])
            return process_attrs(attrs[2:], acc)
        else:
            raise RuntimeError('Invalid error attributes.')

    if type(typestr) not in [str, String]:
        raise RuntimeError('Invalid error type.')

    err = process_attrs(attrs, [])
    try:
        form = assoc(err.attrs, Symbol(':form'))
        err.start_row = form.start_row
        err.start_col = form.start_col
        err.end_row = form.end_row
        err.end_col = form.end_col
        err.filename = form.filename
    except:
        pass

    return err

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

def check_rest_parameters(params):
    if params.count(Symbol('&')) > 1:
        raise ParamError('More than one "&" in the argument list.', params)
    if Symbol('&') in params:
        if params.index(Symbol('&')) != len(params) - 2:
            raise ParamError('Rest argument not at the end of the list.', params)
    for p in params:
        if isinstance(p, list):
            check_rest_parameters(p)

class Function(object):
    def __init__(self, params, body, env):
        if type(params) != List:
            raise ParamError('Invalid argument list; not a list.', params)

        if any(type(i) != Symbol for i in params):
            raise ParamError(
                'Function parameter list should only contain symbols.',
                params)

        check_rest_parameters(params)

        # check if the parameter list is duplicate free
        if len(params) != len(set(params)):
            raise ParamError('Duplicate parameters.', params)

        self.params = params
        self.body = body
        self.env = env

    def call(self, args):
        params = self.params
        if not isinstance(args, (List, list)):
            return create_error(':arg-error',
                                ':msg', 'Function argument list not a List.',
                                ':form', args)
        args = List(args) if not isinstance(args, List) else args

        if len(params) >= 2 and params[-2] == Symbol('&'):
            if len(args) < len(params) - 2:
                return create_error(':arg-error',
                                    ':msg', 'Expected at least {} argument(s) but got {}.'\
                                            .format(len(params) - 2, len(args)),
                                    ':form', args)
        elif len(args) != len(params):
            return create_error(':arg-error',
                                ':msg', 'Expected {} argument(s) but got {}.' \
                                        .format(len(params), len(args)),
                                ':form', args)

        if len(params) >= 2 and params[-2] == Symbol('&'):
            args = args[:len(params) - 2] + [args[len(params) - 2:]]
            params = params[:-2] + params[-1:]

        return eval(self.body, dict(self.env, **dict(zip(params, args))))

    def __repr__(self):
        return '<Function params={} body={}>'.format(self.params, self.body)

class Macro(object):
    def __init__(self, params, body, env):
        if type(params) != List:
            raise ParamError('Invalid parameter list; not a list.', params)

        self.check_params(params)

        self.params = params
        self.body = body
        self.env = env

    def check_params(self, params):
        def flatten(l, acc=[]):
            for i in l:
                if isinstance(i, list):
                    flatten(i, acc)
                else:
                    acc.append(i)
            return acc

        if not isinstance(params, List):
            raise ParamError(
                'Parameter list must be a List not a {}.'.format(type(params).__name__), params)

        check_rest_parameters(params)

        oparams = params
        params = flatten(params)
        if not all(isinstance(i, Symbol) for i in params):
            raise ParamError(
                'Parameters must be symbols.', params)
        params = [i for i in params if i.name != '&']

        if len(params) != len(set(params)):
            raise ParamError('Duplicate parameters.', oparams)

    def expand(self, args):
        try:
            extra_env = destructure(self.params, args)
            return eval(self.body, dict(self.env, **extra_env))
        except ArgError as e:
            return create_error(':arg-error',
                                ':msg', str(e),
                                ':form', args)

    def __repr__(self):
        return '<Macro params={} body={}>'.format(self.params, self.body)

class List(list):
    def __init__(self, *args, **kwargs):
        super(List, self).__init__(*args, **kwargs)
        self.start_row = 0
        self.start_col = 0
        self.end_row = 0
        self.end_col = 0
        self.filename = ''

    def __getitem__(self, key):
        if isinstance(key, slice):
            l = super(List, self).__getitem__(key)
            return List(l)
        else:
            return super(List, self).__getitem__(key)

    def __setitem__(self, key, value):
        super(List, self).__setitem__(key, value)

    def __getslice__(self, i, j):
        return self.__getitem__(slice(i, j))

    def __add__(self, other):
        return List(super(List, self).__add__(other))

    def __radd__(self, other):
        if not isinstance(other, List):
            other = List(other)
        return List(super(List, other).__add__(self))

    def __repr__(self):
        return 'L{}'.format(super(List, self).__repr__())

class Bool(object):
    def __init__(self, v):
        self.value = v
        self.start_row = 0
        self.start_col = 0
        self.end_row = 0
        self.end_col = 0
        self.filename = ''

    def __eq__(self, other):
        if type(other) != Bool:
            other = Bool(other)
        return self.value == other.value

    def __repr__(self):
        return 'B{}'.format(self.value)

class Integer(int):
    def __new__(cls, *args, **kwargs):
        return super(Integer, cls).__new__(cls, *args, **kwargs)

    def __init__(self, n):
        self.start_row = 0
        self.start_col = 0
        self.end_row = 0
        self.end_col = 0
        self.filename = ''

    def __repr__(self):
        return 'N{}'.format(super(Integer, self).__repr__())

class String(str):
    def __new__(cls, *args, **kwargs):
        obj = super(String, cls).__new__(cls, *args, **kwargs)
        obj.start_row = 0
        obj.start_col = 0
        obj.end_row = 0
        obj.end_col = 0
        obj.filename = ''
        return obj

    def __add__(self, other):
        return String(str(self) + str(other))

    def __radd__(self, other):
        return String(str(other) + str(self))

    def __repr__(self):
        return 'S{}'.format(super(String, self).__repr__())

def destructure(params, args):
    if type(params) == List and type(args) != List:
        raise ArgError('Parameter list and the provided arguments do not match.\n'
                       '    Expected a list in the arguments, got: {}'
                       .format(args),
                       args)

    if len(params) >= 2 and params[-2] == Symbol('&'):
        if len(args) < len(params) - 2:
            raise ArgError('Parameter list and the provided arguments do not match.\n'
                           '    Expected at least {} argument(s) but got {}.'
                           .format(len(params) - 2, len(args)),
                           args)

        args = args[:len(params) - 2] + [args[len(params) - 2:]]
        params = params[:-2] + params[-1:]
    elif len(params) != len(args):
        raise ArgError('Parameter list and the provided arguments do not match.\n'
                       '    Expected {} argument(s) but got {}.'
                       .format(len(params), len(args)),
                       args)

    env = {}
    for p, a in zip(params, args):
        if type(p) == Symbol:
            env[p] = a
        elif type(p) == List:
            env.update(destructure(p, a))
        else:
            raise ParamError('Only symbols and lists allowed in parameter list; got an {} instead.'.format(type(p).__name__), p)

    return env

def macro_expand_1(exp, env):
    if type(exp) != List or len(exp) == 0:
        return exp, False

    macro = eval(exp[0], env)
    if isinstance(macro, Error):
        return exp, False

    if not isinstance(macro, Macro):
        return exp, False

    args = exp[1:]
    expanded = macro.expand(args)

    if isinstance(expanded, Error):
        return expanded, False
    else:
        return expanded, True

def macro_expand(exp, env):
    result, is_expanded = macro_expand_1(exp, env)
    if not is_expanded:
        return result, False

    while is_expanded:
        result, is_expanded = macro_expand_1(result, env)

    return result, True

def eval_error(sexp, env):
    assert sexp[0].name == 'error'
    if len(sexp) < 2:
        return create_error(':arg-error',
                            ':msg', 'error expects at least one argument; {} given.'.format(len(sexp) - 1),
                            ':form', sexp)

    error_type = eval(sexp[1], env)
    if type(error_type) != Symbol:
        return create_error(':type-error',
                            ':msg', 'Invalid error type.',
                            ':form', sexp[1])
    attrs = List(eval(i, env) for i in sexp[2:])
    err = Error(error_type, attrs)

    err.filename = sexp.filename
    err.start_row = sexp.start_row
    err.start_col = sexp.start_col
    err.end_row = sexp.end_row
    err.end_col = sexp.end_col

    return err

def eval_error_type(sexp, env):
    assert sexp[0].name == 'error-type'
    if len(sexp) != 2:
        return create_error(':arg-error',
                            ':msg', 'error-type expects exactly one argument; {} given.'.format(len(sexp) - 1),
                            ':form', sexp)

    error = eval(sexp[1], env)
    if type(error) != Error:
        return create_error(':type-error',
                            ':msg', 'error-type argument must be an Error; {} given.'.format(str(type(error))),
                            ':form', sexp)

    return error.type

def eval_error_attrs(sexp, env):
    assert sexp[0].name == 'error-attrs'
    if len(sexp) != 2:
        return create_error(':arg-error',
                            ':msg', 'error-attrs expects exactly one argument; {} given.'.format(len(sexp) - 1),
                            ':form', sexp)

    error = eval(sexp[1], env)
    if type(error) != Error:
        return create_error(':type-error',
                            ':msg', 'error-attrs argument must be an Error; {} given.'.format(str(type(error))),
                            ':form', sexp)

    return error.attrs

def eval_if(sexp, env):
    assert sexp[0].name == 'if'
    if len(sexp) != 4:
        return create_error(':arg-error',
                            ':msg', '`if` form accepts exactly 3 arguments; {} given.'.format(len(sexp) - 1),
                            ':form', sexp)

    cond = eval(sexp[1], env)

    if isinstance(cond, Error):
        return cond

    if cond == Bool(True):
        return eval(sexp[2], env)
    elif cond == Bool(False):
        return eval(sexp[3], env)
    else:
        return create_error(':type-error',
                            ':msg', '`if` condition can only be a boolean; got a {} instead.'.format(type(cond).__name__),
                            ':form', sexp[1])

def eval_quote(sexp, env):
    assert sexp[0].name == 'quote'
    if len(sexp) != 2:
        return create_error(':arg-error',
                            ':msg', '`quote` form accepts exactly one argument; got {} instead.'.format(len(sexp) - 1),
                            ':form', sexp)
    return sexp[1]

def eval_typeof(sexp, env):
    assert sexp[0].name == 'typeof'
    if len(sexp) != 2:
        return create_error(':arg-error',
                            ':msg', '`typeof` form accepts exactly 1 argument; {} given.'.format(len(sexp) - 1),
                            ':form', sexp)

    val = eval(sexp[1], env)
    val_type = {List: Symbol('list'),
                Error: Symbol('error'),
                Symbol: Symbol('symbol'),
                Function: Symbol('function'),
                Macro: Symbol('macro'),
                Bool: Symbol('bool'),
                Integer: Symbol('int'),
                String: Symbol('str')}.get(type(val), None)
    assert val_type != None
    return val_type

def eval_first(sexp, env):
    assert sexp[0].name == 'first'
    if len(sexp) != 2:
        return create_error(':arg-error',
                            ':msg', '`first` form accepts exactly 1 argument; {} given.'.format(len(sexp) - 1),
                            ':form', sexp)
    ret = eval(sexp[1], env)
    if isinstance(ret, Error):
        return ret
    if type(ret) != List:
        return create_error(':type-error',
                            ':msg', '`first` argument must be a list.',
                            ':form', sexp[1])
    if ret == []:
        return create_error(':value-error',
                            ':msg', '`first` argument cannot be an empty list.',
                            ':form', sexp[1])
    return ret[0]

def eval_rest(sexp, env):
    assert sexp[0].name == 'rest'
    if len(sexp) != 2:
        return create_error(':arg-error',
                            ':msg', '`rest` form accepts exactly 1 argument; {} given.'.format(len(sexp) - 1),
                            ':form', sexp)
    ret = eval(sexp[1], env)
    if type(ret) == Error:
        return ret
    if type(ret) != List:
        return create_error(':type-error',
                            ':msg', '`rest` argument must be a list.',
                            ':form', sexp)
    return ret[1:]

def eval_prep(sexp, env):
    assert sexp[0].name == 'prep'
    if len(sexp) != 3:
        return create_error(':arg-error',
                            ':msg', '`prep` form accepts exactly 2 arguments; {} given.'.format(len(sexp) - 1),
                            ':form', sexp)
    first = eval(sexp[1], env)
    rest = eval(sexp[2], env)
    if isinstance(first, Error):
        return first
    if isinstance(rest, Error):
        return rest
    if type(rest) != List:
        return create_error(':type-error',
                            ':msg', '`prep` second argument must be a list.',
                            ':form', sexp)
    return [first] + rest

def eval_iadd(sexp, env):
    assert sexp[0].name == 'iadd'
    if len(sexp) != 3:
        return create_error(':arg-error',
                            ':msg', '`iadd` form accepts exactly 2 arguments; {} given.'.format(len(sexp) - 1),
                            ':form', sexp)

    first = eval(sexp[1], env)
    second = eval(sexp[2], env)

    if isinstance(first, Error):
        return first
    if isinstance(second, Error):
        return second

    if not isinstance(first, Integer) or not isinstance(second, Integer):
        return create_error(':type-error',
                            ':msg', '`iadd` only accepts integers.',
                            ':form', sexp)

    return Integer(first + second)

def eval_imul(sexp, env):
    assert sexp[0].name == 'imul'
    if len(sexp) != 3:
        return create_error(':arg-error',
                            ':msg', '`imul` form accepts exactly 2 arguments; {} given.'.format(len(sexp) - 1),
                            ':form', sexp)

    first = eval(sexp[1], env)
    second = eval(sexp[2], env)

    if isinstance(first, Error):
        return first
    if isinstance(second, Error):
        return second

    if not isinstance(first, Integer) or not isinstance(second, Integer):
        return create_error(':type-error',
                            ':msg', '`imul` only accepts integers.',
                            ':form', sexp)

    return Integer(first * second)

def eval_idiv(sexp, env):
    assert sexp[0].name == 'idiv'
    if len(sexp) != 3:
        return create_error(':arg-error',
                            ':msg', '`idiv` form accepts exactly 2 arguments; {} given.'.format(len(sexp) - 1),
                            ':form', sexp)

    first = eval(sexp[1], env)
    second = eval(sexp[2], env)

    if isinstance(first, Error):
        return first
    if isinstance(second, Error):
        return second

    if not isinstance(first, Integer) or not isinstance(second, Integer):
        return create_error(':type-error',
                            ':msg', '`idiv` only accepts integers.',
                            ':form', sexp)

    if second == 0:
        return create_error(':value-error',
                            ':msg', 'Division by zero.',
                            ':form', sexp)

    return Integer(first / second)

def eval_imod(sexp, env):
    assert sexp[0].name == 'imod'
    if len(sexp) != 3:
        return create_error(':arg-error',
                            ':msg', '`imod` form accepts exactly 2 arguments; {} given.'.format(len(sexp) - 1),
                            ':form', sexp)

    first = eval(sexp[1], env)
    second = eval(sexp[2], env)

    if isinstance(first, Error):
        return first
    if isinstance(second, Error):
        return second

    if not isinstance(first, Integer) or not isinstance(second, Integer):
        return create_error(':type-error',
                            ':msg', '`imod` only accepts integers.',
                            ':form', sexp)

    if second == 0:
        return create_error(':value-error',
                            ':msg', 'Division by zero.',
                            ':form', sexp)

    return Integer(first % second)

def eval_ineg(sexp, env):
    assert sexp[0].name == 'ineg'
    if len(sexp) != 2:
        return create_error(':arg-error',
                            ':msg', '`ineg` form accepts exactly 1 argument; {} given.'.format(len(sexp) - 1),
                            ':form', sexp)

    first = eval(sexp[1], env)

    if isinstance(first, Error):
        return first

    if not isinstance(first, Integer):
        return create_error(':type-error',
                            ':msg', '`ineg` only accepts integers.',
                            ':form', sexp)

    return Integer(-first)

def eval_ilt(sexp, env):
    assert sexp[0].name == 'ilt'
    if len(sexp) != 3:
        return create_error(':arg-error',
                            ':msg', '`ilt` form accepts exactly 2 arguments; {} given.'.format(len(sexp) - 1),
                            ':form', sexp)

    first = eval(sexp[1], env)
    second = eval(sexp[2], env)

    if isinstance(first, Error):
        return first
    if isinstance(second, Error):
        return second

    if not isinstance(first, Integer):
        return create_error(':type-error')
    if not isinstance(second, Integer):
        return create_error(':type-error')

    return Bool(first < second)

def eval_eq(sexp, env):
    assert sexp[0].name == 'eq'
    if len(sexp) != 3:
        return create_error(':arg-error',
                            ':msg', '`eq` form accepts exactly two arguments; {} given.'.format(len(sexp) - 1),
                            ':form', sexp)
    first = eval(sexp[1], env)
    second = eval(sexp[2], env)

    if type(first) != List and type(second) != List:
        return Bool(True) if first == second else Bool(False)
    elif first == second == []:
        return Bool(True)
    else:
        return Bool(False)

def eval_apply(sexp, env):
    assert sexp[0].name == 'apply'
    if len(sexp) != 3:
        return create_error(':arg-error',
                            ':msg', '`apply` expects 2 arguments; {} given.'.format(len(sexp) - 1),
                            ':form', sexp)

    func = eval(sexp[1], env)
    if isinstance(func, Error):
        return func
    if not isinstance(func, Function):
        return create_error(':type-error',
                            ':msg', '`apply` first argument must be a function; got {}.'.format(func),
                            ':form', sexp[1])
    args = eval(sexp[2], env)
    if isinstance(args, Error):
        return args
    if not isinstance(args, (list, List)):
        return create_error(':type-error',
                            ':msg', 'A list not passed as function argument list.',
                            ':form', args)
    return func.call(args)

def eval(exp, env):
    if type(exp) == List:
        return eval_sexp(exp, env)
    elif type(exp) == Integer:
        return exp
    elif type(exp) == String:
        return exp
    elif type(exp) == Bool:
        return exp
    elif type(exp) == Error:
        return exp
    elif exp == Symbol('nil'):
        return List()
    elif type(exp) == Symbol and exp.name.startswith(':'):
        return exp

    if exp not in env:
        return create_error(':variable-error',
                            ':msg', 'Unbound variable: {}'.format(exp.name),
                            ':form', exp)

    return env[exp]

def eval_sexp(sexp, env):
    if sexp == []:
        return List()

    first = sexp[0]

    if first == Symbol('fn'):
        if len(sexp) != 3:
            return create_error(':form-error',
                                ':msg', 'Invalid fn expression.',
                                ':form', sexp)
        try:
            return Function(sexp[1], sexp[2], env)
        except ParamError as e:
            return create_error(':param-error',
                                ':msg', str(e),
                                ':form', sexp[1])
    if first == Symbol('mac'):
        if len(sexp) != 3:
            return create_error(':form-error',
                                ':msg', 'Invalid mac expression.',
                                ':form', sexp)
        try:
            return Macro(sexp[1], sexp[2], env)
        except ParamError as e:
            return create_error(':param-error',
                                ':msg', 'Invalid macro parameter list: ' + str(e),
                                ':form', sexp[1])

    map = {Symbol('if'): eval_if,
           Symbol('quote'): eval_quote,
           Symbol('prep'): eval_prep,
           Symbol('typeof'): eval_typeof,
           Symbol('first'): eval_first,
           Symbol('rest'): eval_rest,
           Symbol('eq'): eval_eq,
           Symbol('error'): eval_error,
           Symbol('error-type'): eval_error_type,
           Symbol('error-attrs'): eval_error_attrs,
           Symbol('apply'): eval_apply,
           Symbol('iadd'): eval_iadd,
           Symbol('imul'): eval_imul,
           Symbol('idiv'): eval_idiv,
           Symbol('imod'): eval_imod,
           Symbol('ilt'): eval_ilt,
           Symbol('ineg'): eval_ineg}

    if type(first) == Symbol and first in map:
        return map[first](sexp, env)

    # it must be a function or macro call, or an integer index.

    first = eval(sexp[0], env)

    if isinstance(first, Integer):
        if len(sexp) != 2:
            return create_error(':arg-error',
                                ':msg', 'Index form with more than one argument.',
                                ':form', sexp)

        second = eval(sexp[1], env)
        if not isinstance(second, List):
            return create_error(':type-error',
                                ':msg', 'Only lists can be indexed.',
                                ':form', sexp[1])

        if first < 0 or first > len(second) - 1:
            return create_error(':index-error',
                                ':msg', 'Index {} not valid for the given list.',
                                ':form', sexp[0])

        return second[first]

    if not isinstance(first, (Function, Macro)):
        return create_error(':value-error',
                            ':msg', 'Not a function or a macro: {}'.format(first),
                            ':form', sexp[0])

    args = List(sexp[1:])
    args.filename = sexp.filename
    args.start_row = sexp.start_row
    args.start_col = sexp.start_col
    args.end_row = sexp.end_row
    args.end_col = sexp.end_col

    if isinstance(first, Function):
        # evaluate arguments.
        args = List([eval(i, env) for i in args])
        if len(sexp) > 1:
            args.start_row = sexp[1].start_row
            args.start_col = sexp[1].start_col
            args.end_row = sexp[-1].end_row
            args.end_col = sexp[-1].end_col
        else:
            args.start_row = sexp.start_row
            args.start_col = sexp.start_col
            args.end_row = sexp.end_row
            args.end_col = sexp.end_col
        args.filename = sexp.filename

        return first.call(args)
    elif isinstance(first, Macro):
        # now expand the macro.
        expanded = first.expand(args)

        # evaluate the result of expansion.
        return eval(expanded, env)
    else:
        return create_error(':value-error',
                            ':msg', 'Expected a macro or a function, got: {}'.format(first),
                            ':form', first)
