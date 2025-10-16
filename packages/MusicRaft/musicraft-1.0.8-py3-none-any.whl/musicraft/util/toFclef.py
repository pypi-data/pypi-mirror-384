#!/usr/bin/python3
'''
Background:
    I need to deal with two realisations of the smae group of tunes: one for accordions, one for cello(s).
    I'm reluctant to sue abpp for a numer of reasons, the main one being that musicraft isn't geared up to it!
    With %%format and/or %%abc-include, you can do some clever stuff, but not enough.
'''
import sys,os, re

from arghandler import ArgHandler

re_voice = re.compile(r'(\s*V\:)(\S+)(.*)(treble-8)(.*)')

# from symbol import with_item

class ToFclef(ArgHandler):
    def main(self):
        self.process_all_keyword_args()
        if input_filename := self.next_arg():
            input_file = open(input_filename, 'r')
        else:
            input_file = sys.stdin

        if output_filename := self.next_arg():
            output_file = open(output_filename, 'w')
        else:
            output_file = sys.stdout

        self.no_more_positional_args()

        with output_file:
            for line in input_file:
                if matches := re_voice.match(line):
                    line_parts = list(matches.groups())
                    # print(list(enumerate(line_parts)))
                    line_parts[3] = 'bass'
                    line = ''.join(line_parts)+'\n'
                output_file.write(line)
                if matches:
                    output_file.write("%%transpose -12  # added by 'toFclef.py' which also changes clef above!\n")

if __name__ == '__main__':
    ToFclef().main()
