#!/usr/bin/python3
# -*- coding: utf-8 -*-
""" Large = 'Little argument engine' - a utility class."""
import sys, os, shlex, glob

class ArgHandler:
    # N.B. This code started life as part of 'walker.py'.

    name_ = "base argument handler class"
    verbosity = 0
    prefix_ = ''   # maybe None better but this lazier
    myExts = ()

    def __init__(self):
        self.program_name, *self.argv = sys.argv

    def vprint(self, this_verbosity, *pp, file=sys.stderr, **kw):
        if self.verbosity >= this_verbosity:
            return print(*pp, file=file, **kw)

    def process_all_keyword_args(self):
        while self.process_next_keyword_arg():
            pass

    def next_arg(self, default=None):
        if not self.argv:
            return default
        arg = self.argv.pop(0)
        if arg == '--':
            return default
        return arg

    def next_keyword_arg(self):
        arg = self.next_arg()
        if not arg:
            return
        if arg[0]=='-':
            self.latest_kw_arg = arg
            return arg
        self.argv.insert(0, arg)

    def next_float_arg(self, default=None):
        v= self.next_arg(default)
        if v is None:
            raise ValueError(f"missing float/percentage value after keyword '{self.latest_kw_arg}'")
        sReal, *rest = str(v).split('%')
        real = float(sReal)
        if rest:
            if rest:
                raise ValueError("invalid real/percentage value")
            real /= 100.0
        return real

    def next_int_arg(self, default=0):
        v = self.next_arg(default)
        if v is None:
            raise ValueError(f"missing integer value after keyword '{self.latest_kw_arg}'")
        return int(v)

    def process_keyword_arg(self, a):
        if a in ('-v', '--verbose'):
            self.verbosity += 1
            return a
        if a in ('-q', '--quiet'):
            self.verbosity -= 1
            return a

        # unrecognized args follow through to....
        print(
                "\n"
                "all utilities based around the 'ArgHanlder' class (also) accept the arguments (don't enter the quotes!):\n"
                "'--help' or equivalently '-h'\n"
                "\trequests help information about this command."
                "\n"
                "'--verbose' or equivalently '-v'\n"
                "\trequests verbose operation, i.e. more textual output; repeat this argument for even more!"
                "\n"
                "'--quiet' or equivalently '-q'\n"
                "\trequests quiet operation, i.e. less textual output;"
              )
        if a in ('-h', '--help'):
            sys.exit(0)
        print("keyword '%s' not understood." % a)
        sys.exit(991)

    def process_next_keyword_arg(self):
        a = self.next_keyword_arg()
        if a is not None:
            return self.process_keyword_arg(a)

    def no_more_positional_args(self):
        if self.argv:
            raise ValueError(f"extraneous argument(s) '{self.argv}' passed to '{self.program_name}'.")

    def main(self):
        #print (os.getcwd())
        self.process_all_keyword_args()
        self.no_more_positional_args()

if __name__ == '__main__':
    ArgHandler().main()  # our class is both a base class and a dummy class
