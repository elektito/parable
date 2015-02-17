from parable import Symbol, String, Integer, List, Function, Macro

def pprint_bool(form):
    return '#t' if form else '#f'

def pprint_symbol(form):
    return form.name

def pprint_string(form):
    return '"{}"'.format(form)

def pprint_integer(form):
    return '{}'.format(form)

def pprint_function(form):
    if form.params == List():
        return '(fn () {})'.format(pprint(form.body))
    else:
        return '(fn {} {})'.format(pprint(form.params), pprint(form.body))

def pprint_macro(form):
    if form.params == List():
        return '(mac () {})'.format(pprint(form.body))
    else:
        return '(mac {} {})'.format(pprint(form.params), pprint(form.body))

def pprint_list(form):
    if len(form) == 2 and form[0] == Symbol('quote'):
        return "'{}".format(pprint(form[1]))
    if len(form) == 2 and form[0] == Symbol('backquote'):
        return "`{}".format(pprint(form[1]))
    if len(form) == 2 and form[0] == Symbol('unquote'):
        return ",{}".format(pprint(form[1]))
    if len(form) == 2 and form[0] == Symbol('unquote-splicing'):
        return ",@{}".format(pprint(form[1]))
    if form == []:
        return 'nil'

    return '({})'.format(' '.join(pprint(i) for i in form))

def pprint(form):
    if type(form) == list:
        form = List(form)
    if type(form) == str:
        form = String(form)
    if type(form) == int:
        form = Integer(form)

    result = {
        Symbol: pprint_symbol,
        bool: pprint_bool,
        Integer: pprint_integer,
        String: pprint_string,
        Function: pprint_function,
        Macro: pprint_macro,
        List: pprint_list
    }[type(form)](form)

    return result
