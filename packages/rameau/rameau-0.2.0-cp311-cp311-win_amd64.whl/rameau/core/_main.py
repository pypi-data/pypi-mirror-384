import sys
from rameau.wrapper.cwrapper import _main

def _run_main():
    args = sys.argv
    my_args = ''
    if len(args) > 1:
        my_args = my_args + ' '.join(args[1:])
    _main(my_args)
