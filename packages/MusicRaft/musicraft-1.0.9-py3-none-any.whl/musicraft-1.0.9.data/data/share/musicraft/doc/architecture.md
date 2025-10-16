# MusicRaft
## Architecture

Architecture is arguably too big a word for the way `musicraft` has been
put (thrown?) together but let's use our imagination.

Musicraft is in fact a very lightweight (and very limited!) IDE
implemented as 'the raft' on top of which the plugin `abcraft` is loaded. (Actually,
the architechtural split isn't quite so clean; the raft contains quite
some ABC-specific code!)

Other real and prospective plugins are described in
[Extensions](extensions.md)



