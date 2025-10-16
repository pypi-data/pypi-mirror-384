#!/usr/bin/env python
'''
Warning:
    This so-called 'utility' script simply a solution to a local requirement of mine.
    It is not even an elegant solution at that!
Background:
    I need to deal with two realisations of the same group of tunes: one for accordions, one for cello(s).
    I'm reluctant to sue abpp for a numer of reasons, the main one being that musicraft isn't geared up to it!
    With %%format and/or %%abc-include, you can do some clever stuff, but not enough.
    UPDATE! In practice I also need the reverse operation, so I can edit teh cello part directly to insert
    accents and fingering. So I want to make a more  generalized converter.

Warning:
    The diesign of thi sstuff is still pretty fluid. Tihs script may morph into something more generalized,
    possibly under a new name... and I really should start using Pathlib!
'''
import sys,os, re

from arghandler import ArgHandler

class ToFclef(ArgHandler):
    re_voice = re.compile(
r'(\s*V\:)(\S+)(.*)(treble-8|treble|bass)(.*)'
    )
    re_transpose = re.compile(
r'%%transpose\s+(-?\d+).*'
    )  # don't capture what we don't want to checlk or reuse!
    re_chord = re.compile(
r'"[a-g|A-G][b|#]?[m]?"'
    )  # don't capture what we don't want to checlk or reuse!

    def main(self):
        print(os.getcwd())
        self.process_all_keyword_args()
        if input_filename := self.next_arg():
            # breakpoint()
            input_file = open(input_filename, 'r')
        else:
            input_file = sys.stdin

        if output_filename := self.next_arg():
            if os.path.isdir(output_filename):
                output_filename += f'/{os.path.split(input_filename)[1]}'
            output_file = open(output_filename, 'w')
        else:
            output_file = sys.stdout

        self.no_more_positional_args()

        with output_file:
            voice_line_matches = None
            for line in input_file:
                if voice_line_matches: # last time around
                    if transpose_line_matches := self.re_transpose.match(line):
                        transpose_line_parts = list(transpose_line_matches.groups())
                        self.vprint(1, f"transpose_line_parts={list(enumerate(transpose_line_parts))}")
                        old_semitones = int(transpose_line_parts[0])  # we only saved ()bracketed) the number
                        new_semitones += old_semitones
                        self.vprint(1, f'{old_semitones=} {new_semitones=} ')
                    if new_semitones:
                        output_file.write(
f"%%transpose {new_semitones}  # added by 'otherFclef.py' which also changed 'V:...' above!\n"
                        )
                    if transpose_line_matches:
                        continue
                if voice_line_matches := self.re_voice.match(line):
                    voice_line_parts = list(voice_line_matches.groups())
                    self.vprint(1, f"voice_line_parts={list(enumerate(voice_line_parts))}")
                    old_clef = voice_line_parts[3]
                    new_clef, new_semitones = {'treble':   ('bass', -12),
                                               'treble-8': ('bass', -12),
                                               'bass':     ('treble', 12)
                                               } [old_clef]
                    self.vprint(1, f'{old_clef=} {new_clef=} {new_semitones=} ')
                    voice_line_parts[3] = new_clef
                    line = ''.join(voice_line_parts)+'\n'
                output_file.write(line)

if __name__ == '__main__':
    ToFclef().main()
