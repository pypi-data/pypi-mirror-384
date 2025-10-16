#!/usr/bin/env python3
"""
'run_muscraft.py' is practically equivalent to 'python -m musicraft', but may be more convenient in
some operational contexts.
"""

# -----------------------------------------------------------------------------
# import the code of the plugins we intend to launch 'on the raft':
from musicraft.abcraft import AbcRaft
if 0:
    from musicraft.pyraft import PyRaft  # currently disabled
# -----------------------------------------------------------------------------
# import the code to start 'the raft':
from musicraft.__main__ import MusicMain

# -----------------------------------------------------------------------------
# now call the 'raft' with the 'abcraft' plugin;
#
MusicMain().main(Plugins=(AbcRaft,
                          # PyRaft,  # currently disabled
                          ))
