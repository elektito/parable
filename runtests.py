from read import Reader, ReadError
from parable import eval as eval_form, Symbol
from load import load

def run_tests(f, env):
    passed = 0
    failed = 0
    error = 0

    reader = Reader(f)
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
            error += 1

    return passed, failed, error

if __name__ == '__main__':
    from sys import argv
    if len(argv) < 3 or '--' not in argv or argv.index('--') == len(argv) - 1:
        print
        print 'usage: {} [libraries] -- test-files'.format(argv[0])
        print
        exit(11)

    sep = argv.index('--')
    libraries = argv[1:sep]
    test_files = argv[sep+1:]

    env = {}
    for lib in libraries:
        try:
            with open(lib) as f:
                env = load(f, env)
        except (ReadError, LoadError) as e:
            print 'Error reading library file {}: {}'.format(lib, e)
            exit(12)

    passed = failed = error = 0
    for test_file in test_files:
        try:
            with open(test_file) as f:
                p, f, e = run_tests(f, env)
                passed += p
                failed += f
                error += e
        except ReadError as e:
            print 'Error while running test file {}: {}'.format(test_file, e)
            exit(13)

    print 'Total tests:', passed + failed + error
    print '   Successful:', passed
    print '   Failed:', failed
    print '   Error:', error
