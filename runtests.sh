#!/bin/sh

python test.py && python load.py -l stdlib.lisp -t test-stdlib.lisp
