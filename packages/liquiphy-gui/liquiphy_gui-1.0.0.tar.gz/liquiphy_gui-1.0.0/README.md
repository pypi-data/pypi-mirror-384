# liquiphy_gui

A quick and dirty GUI interface to the liquidsfz command-line using python's subprocess.

Need to listen to an .sfz file without a lot of hassle? Use liquiphy_gui!

	$ liquiphy-gui <path-to-sfz>

The above command loads the given .sfz file in a liquidsfz instance and
automatically connects the Jack MIDI input and Jack audio outputs to the first
available (physical) ports, displaying the SFZ name and ports connected in a
simple dialog.

Hit the Escape key or ctrl-Q to exit.

## Install

You must install liquidsfz first for this package to work. To install:

	$ git clone https://github.com/swesterfeld/liquidsfz.git

Follow the instructions found in the liquidsfz README to install liquidsfz.

Install this package (liquiphy_gui) using python pip:

	$ pip install liquiphy_gui

...or...

	$ python3 -m pip install liquiphy_gui

## File associations

