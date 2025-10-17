#!/usr/bin/env python3
"""
This in example of how to customise the (default) settings of musicraft.
The script name reflects the fact that the primary customisation in effect
concerns "Timidity", but several other possibilities are shown, some of
 them in 'commented out' form.
Copyright 2020 Larry Myerscough
"""
import musicraft
print(f"!using musicraft from {musicraft.__file__}!")
# -----------------------------------------------------------------------------
# import the code of the one and only plugin we intend to launch 'on the raft':
from musicraft.abcraft import AbcRaft
# -----------------------------------------------------------------------------
# import the code to start 'the raft':
from musicraft.__main__ import MusicMain
# -----------------------------------------------------------------------------
# but first let's do some tweaking (customisation)...
# I have chose to use 'if 1' 'if 0 ' rather than the traditional practice of
# 'commenting out to enable/disable particulr customizations
# -----------------------------------------------------------------------------
# select a specific MIDI output port name (this is useful for my ubuntu setup)
if 0:  # disabled because I haven't testing this for years
    from musicraft.abcraft.midiplayer import MidiPlayer
    MidiPlayer.outputPort = 'TiMidity:TiMidity port 0 128:0'

# -----------------------------------------------------------------------------
# example of how to overrule text encoding to use when creating PDF.
# 'standard' musicraft imposes 'latin1' encoding as a workaround for obscure (to me) problems
# (The underlying problem disappears if I use the 7-bit ASCII sequences for accented characters
# as described in the abc plus manual... but that oughtn't to be necessary in this day and age!)
#
if 0:  # disabled because I changed this just before release so don't fully trust it.
    import locale
    from musicraft.raft import External
    External.encoding = locale.getpreferredencoding() # this is arguably the correct approach!

# Also include date in PDF derived iva '.ps' file.
#
if 1:  # enabled - I use this customization daily so I trust it!
    from musicraft.abcraft.external import Ps2PDF
    import datetime
    # N.B. time stamped into pdf name is start-up time of musicraft, not derivation time of PDF
    Ps2PDF.fmtNameOut = f'%s-{datetime.date.today().strftime("%d_%b_%Y")}.pdf'

# Produce PDFs both via the svg and postscript route and make it clear which is which.
# I find this handly when This is particularly handy when using special ps or svg definitions
# in fmt files,e.q. for strange note-heads for unusual percussion instruments.
if 0:  # disabled because 'normal people' may well see the extra PDF as unnecessary clutter.
    from musicraft.abcraft.external import Svg2PDF
    Svg2PDF.fmtNameOut = '%s-svg.pdf' # currently this only works under Linux.

# -----------------------------------------------------------------------------
# enable the following lines to select a different directory for the abc2midi program.
if 0:  # disabled; just here for example purposes.
    from musicraft.abcraft.external import Abc2midi
    # n.b. the folloing only has effect if musciraft is started with '-X' or '--external'!
    Abc2midi.exec_dir = '/usr/local/bin/'  # perhaps perventing use of abc2midi from user's local path
# ... and maybe also tweak the way musicraft parses the output of abc2mdi ...
    if 0:  # doubly disabled because I'm not sure of the background of this!
        Abc2midi.reMsg = r'.*in\s+line-char\s(\d+)\-(\d+).*'
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# # enable the following lines to select a different docking scheme
# # for the various components of 'the raft'.
if 0:  # disabled because tis han't been tested for quite some time.
    from musicraft import QtCore, EditBook, StdBook, DisplayBook
    EditBook.whereToDock = QtCore.Qt.RightDockWidgetArea
    StdBook.whereToDock = QtCore.Qt.RightDockWidgetArea
    DisplayBook.whereToDock = QtCore.Qt.LeftDockWidgetArea


# -----------------------------------------------------------------------------
# 'PyRaft' is included on teh standard startup but is not needed for general use,
# sl let's disable it!
# FreqRaft is currently disabled because it is (forever?) unfinished.
#
MusicMain().main(Plugins=(AbcRaft,))
