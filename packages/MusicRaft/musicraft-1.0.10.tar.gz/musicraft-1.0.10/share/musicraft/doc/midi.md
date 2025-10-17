# MusicRaft
## Midi support
Note: this all refers to MIDI playback/synthesis. MIDI input devices (keyboards etc.)
are not supported at all.

All progress/error mesages relating to layng midi files appear in the
`system` tab of th eerror/output window; only mesages relating to
the `abc2midi` midi-creator program appear in the `Abc2Midi` tab.

Musicraft creates and re-creates MIDI files on the fly by running `abc2midi` 
each time the ABC file is changed . This MIDI file can be played using the 
`MIDI` entry menu of the  top menu bar. As each note is played, the corresponding note
(or rest) symbol in the score is highlighted with a red circle.
This can be is very handy.

Musicraft uses the
[MIDO](https://mido.readthedocs.io/en/latest/index.html)
package with the usual backend - `rtmdi`.

By default, the most recently defined midi output device; this works
find for casual users who run a synthesizer server and have no hardware
attached to a hardware midi port. This can be overridden via the menu command
`Midi` / `Select Midi Output`.

If absolutely no midi device is available the whole `Midi` menu will not be
shown at all.

### Windows ###

MIDI output works on Windows 10 with the standard
Microsoft GS wavetable software synthesizer, which is usually present.
There are allegedly much better synthesizers out there, but this one is quite good enough
for detecting audible bloopers in your music!

### MacOS ###

*Note*  I am not a regular Mac user. I expect that there is gentler
more correct procedure to achieve what I decribe below!

Midi output also works fine On Mac OSX, but you may well first need to
make a synthesizer available. My old notes tell me that I once got
`simplesynth` up and running but the details elude me.

'fluidsynth' also works on MacOS but you need to install it yourself,
e.g. ...

`brew intall fluidsynth`

... and start it with ...

`fluidsynth -a coreaudio [e.g.soundfont.sf2]`

substituting the full pathname of your soundfont file.

If you omit the filename, fluidsynth defaults to a soundfont file
that isn't there! If you're not much concerned with the finer
aspects of soundfonts, I suggest you download the `GeneralUser` font from...

https://schristiancollins.com/generaluser.php

... and extract the `.sf2` file from there.

## Linux ##

### MX-Linux ###
I currently use the midi synthesiser 'fluidsynth' under Mx Linux.
The MX packet installer has convenient entries for not only
fludsynth itself but also a number of suitable soundfonts of which
I use `fluidr3mono-gm-soundfont`.

When running fluidsynth via systemd, the choice of soudfont (SOUND_FONT=)
can be specified in /etc/default; it is in some cases necessary also
to specify additional options (OTHER_OPTS) in this file.
The fluidsynth daemon typically shows up in the output of `ps ax` as follows:

   1884 ?        SLsl  17:55 /usr/bin/fluidsynth -is /usr/share/sounds/sf3/default-GM.sf3

### Ubuntu Linux ###

My older test environment for MIDI suport had the Timidity
synthesiser running as a 'daemon' on an Ubuntu Linux platform. 
This typically showed up in the output of `ps ax` as follows:

 1388 ?        S      1:53 timidity -iA -B2,8 -Os

One can, of course, choose to use fluidsynth under Ubuntu. Some recent releases of
Ubuntu use the `pipewire` (as opposed  to `alsa`) audio subsystem. It may be necessary 
to pass the option `-a pipewire` to the fluidsynth server in such cases.

### Other Linux distributions ###

I haven't propely tested any other Linux distributions. When I find the time
to do so, I will add any necessary advice here.
