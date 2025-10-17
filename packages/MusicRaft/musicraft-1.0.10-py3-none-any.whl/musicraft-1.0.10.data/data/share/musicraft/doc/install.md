MusicRaft - Installation notes
=
____Windows____

On Windows, you may well need to install python3 yourself;
I found that when I typed `python3` at a command prompt, but it wasn't
installed, Windows 10 helpfully diretred to the correct installation web page. 
If you're less lucky, just browse to <https://www.python.org/downloads/windows/>
and choose the most recent suitable Windows installer.

Musicraft is dependent on the `rtmidi` package; this is handled
automatically... but installation of `rtmidi` on Microsoft Windows depends
on the presence of the correct version of `msvcp140.dll` (or similar) in the correct
directory.... which is not yet handled automatically. One way to achieve this
is to install the so-called 'Microsoft Visual Studio redistributables'. After doing this, there
will be a start menu item to start a 'Developer command promptfor MSVC 2022'
(or similar). If you run ...

`python3 -m pip musicraft`

.. from here, it will find the necessary compilation tools.

____MacOS____

The situation with MAC OSX depends on which release you are using;
This link explains the situation with MAC OSX Catalina:
<https://apple.stackexchange.com/questions/376077/is-usr-bin-python3-provided-with-macos-catalina>

