from parable import eval as eval_form, Error, Symbol
from read import Reader, ReadError, EofReadError
from load import print_exception, print_error, LoadError, LoadWarning, load
from pprint import pprint

def main():
    try:
        env = {}
        for lib in ['stdlib.lisp', 'bq.lisp']:
            with open(lib) as f:
                try:
                    env.update(load(f, lib, env))
                except (LoadError, LoadWarning) as e:
                    print_exception(e)
                    exit(2)

        while True:
            expr = raw_input('* ')
            try:
                form = Reader(expr, '<string>').read()
                result = eval_form(form, env)
            except ReadError as e:
                print_exception(e)
            if isinstance(result, Error):
                print_error(result)
            print pprint(result)

            env[Symbol('_')] = result
    except KeyboardInterrupt:
        print

if __name__ == '__main__':
    main()
