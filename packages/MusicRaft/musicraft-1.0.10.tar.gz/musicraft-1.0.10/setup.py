"""
MusicRaft - setup.py

Note that this file has become rather bloated with tweaks relating to installation. This will change
(into bloaat elsewhere?!) when I move away for the use of setup.py to more modern methods.
"""

import sys, os, pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

SHARE = pathlib.Path('share') / 'musicraft'
# The text of the README file
blurb_doc_name = "README.md"
README = (SHARE / 'doc' / blurb_doc_name).read_text(encoding="utf-8")

# effectively copy the above readme file to the top level so that it's contents get displayed at top level in gitlab:
# Note: a symbolic link won't cut the mustard (but it's an open issue!).
# The long-hand copy does, however, mean we can adjust the location of some internal links!
#
print(f"copying and adjusting {blurb_doc_name}")
(HERE / blurb_doc_name).write_text(README.replace('(./', '(share/musicraft/doc/'), encoding="utf-8")

share_dirs = [str(SHARE / Dir) for Dir in [
                    'Linux/bin',
                    'OSX/bin',
                    'Windows/post-install',
                    'Windows/abcm2ps-8.14.4',
                    'Windows/abcmidi_win32_mingw64',
                    'Windows/abcmidi_win32',
                    'abc',
                    'doc',
                    'pixmaps']]

share_dirs_here = [str(HERE / share_dir) for share_dir in share_dirs]

data_files = [(share_dir, [os.path.join(share_dir, one_exec) for one_exec in os.listdir(share_dir_here)])
            for share_dir, share_dir_here in zip(share_dirs, share_dirs_here)]

# print(*[f"{his}... {mine}" for his, mine in data_files], sep='\n\n')

with (HERE / 'musicraft' / '__init__.py').open(mode="r", encoding="utf-8") as _init_file:
    version_str = (_init_file.readline().strip().replace("version = ", ""))[1:-1]
# (for debugging)...print(data_files) print(README)
# print(f'{version_str=}')
# sys.exit(0)

# This call to setup() does all the work
setup(name = 'MusicRaft',
    version = version_str,
    description='GUI for abcplus music notation.',
    long_description=README,
    long_description_content_type="text/markdown",
    url='https://gitlab.com/papahippo/MusicRaft',
    author = "Larry Myerscough",
    author_email='hippostech@gmail.com',
    packages=find_packages(),
    data_files=data_files,
    scripts=['bin/musicraft_custom.py', 'bin/run_musicraft.py', 'bin/musicraft_cello.py', 'bin/musicraft.bat',
             ],
    license='LICENSE.txt',
    install_requires=[
        "python-rtmidi", # doesn't get imported as such but its backend is needed by 'mido'
        "mido >= 1.2.0", # release stipulation is easy way to ensure 'rtmidi' backend is used.
        #"pyqtgraph >= 0.10.0",  # only for freqraft plugin
        "lxml",
        "numpy",
        # picks up bad version.. "pyside2",
        "pyqt5",
        "pyqtwebengine",
        "pdfrw",  # for exporting score to PDF
        "ghostscript",  # for ps2pdf external command

    ],
)
