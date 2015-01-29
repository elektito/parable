from cStringIO import StringIO

def eval_if(sexp, env):
    assert sexp[0] == 'if'
    assert len(sexp) == 4
    cond = eval(sexp[1], env)
    if cond == []:
        return eval(sexp[3], env)
    else:
        return eval(sexp[2], env)

def eval_quote(sexp, env):
    assert sexp[0] == 'quote'
    assert len(sexp) == 2
    return sexp[1]

def eval_atom(sexp, env):
    assert sexp[0] == 'atom'
    val = eval(sexp[1], env)
    if type(val) == list:
        return []
    else:
        return 't'

def eval_car(sexp, env):
    assert sexp[0] == 'car'
    assert len(sexp) == 2
    ret = eval(sexp[1], env)
    assert type(ret) == list
    return ret[0]

def eval_cdr(sexp, env):
    assert sexp[0] == 'cdr'
    assert len(sexp) == 2
    ret = eval(sexp[1], env)
    assert type(ret) == list
    return ret[1:]

def eval_cons(sexp, env):
    assert sexp[0] == 'cons'
    assert len(sexp) == 3
    car = eval(sexp[1], env)
    cdr = eval(sexp[2], env)
    assert type(cdr) == list
    return [car] + cdr

def eval_eq(sexp, env):
    assert sexp[0] == 'eq'
    assert len(sexp) == 3
    first = eval(sexp[1], env)
    second = eval(sexp[2], env)
    if type(first) != list and type(second) != list:
        return 't' if first == second else []
    else:
        return []

def eval(exp, env):
    if type(exp) == list:
        return eval_sexp(exp, env)

    if exp not in env:
        print 'Undefined variable:', exp
        exit(1)

    return env[exp]

def eval_sexp(sexp, env):
    if sexp == []:
        return []

    car = sexp[0]

    if car in ('fn', 'mac'):
        assert len(sexp) == 3
        return sexp

    map = {'if': eval_if,
           'quote': eval_quote,
           'cons': eval_cons,
           'atom': eval_atom,
           'car': eval_car,
           'cdr': eval_cdr,
           'eq': eval_eq}

    if type(car) == str and car in map:
        return map[car](sexp, env)

    # it must be a function or macro call then.

    car = eval(sexp[0], env)
    assert type(car) == list
    assert type(car[1]) == list
    assert len(car) == 3

    params = car[1]
    body = car[2]
    args = sexp[1:]

    if len(args) != len(params):
        print 'Expected {} argument(s) but got {}.'.format(len(params), len(args))
        exit(2)

    if car[0] == 'fn':
        # evaluate arguments.
        args = [eval(i, env) for i in args]

        return eval(body, dict(env, **dict(zip(params, args))))
    elif car[0] == 'mac':
        expanded = eval(body, dict(env, **dict(zip(params, args))))
        return eval(expanded, env)
    else:
        print 'Expected a macro or a function, got:', car
        exit(2)

def read_item(f):
    item = ''
    b = f.read(1)
    while b and b not in '() \n':
        item += b
        b = f.read(1)
    if not b:
        print 'Unexpected end of file.'
        exit(1)
    f.seek(-1, 1)
    return item

def read_list(f):
    b = f.read(1)
    if not b or b != '(':
        print 'Expected "(".'
        exit(1)

    items = []

    while True:
        b = f.read(1)
        while b and b in ' \n':
            b = f.read(1)
        if not b:
            print 'Unexpected end of file.'
            exit(1)

        if b == ')':
            return items

        f.seek(-1, 1)
        if b == '(':
            items.append(read_list(f))
        else:
            items.append(read_item(f))

def read(f):
    b = f.read(1)
    if not b:
        print 'Unexpected end of file.'
        exit(1)

    f.seek(-1, 1)
    if b == '(':
        return read_list(f)
    else:
        return read_item(f)

def parse_str(s):
    return read(StringIO(s))
