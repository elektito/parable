#!/bin/sh

python test.py && python load.py -l stdlib.lisp bq.lisp -t test-stdlib.lisp test-bq.lisp
