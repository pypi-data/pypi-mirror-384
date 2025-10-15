# simple_carla

An easy-to-use, object-oriented interface to the carla plugin host.

## Installation

(Not so easy 😒)

You must install carla (including python resources), for this package to work.
After installing carla, check that the following directories exist on your
system:

* /usr/local/lib/carla OR /usr/lib/carla
* /usr/local/share/carla OR /usr/share/carla

On my machine, running carla --version produces the following output:

	Using Carla version 2.6.0-alpha1
	  Python version: 3.10.12
	  Qt version:     5.15.3
	  PyQt version:   5.15.6
	  Binary dir:     /usr/local/lib/carla
	  Resources dir:  /usr/local/share/carla/resources

Checking with "apt-file", it appears that the python resources are not packaged
in the official Debian / Ubuntu repository. You may have to download, build,
and install from source. (I did.)

If you do install from source, you might want to look at tweaking the "-mtune" option in the compiler flags. When I compiled, I replaced every instance of "-mtune=generic" with "-mtune=native -march-native". Since you are building for your machine only, this flag is appropriate.

> For more information, see [GCC optimization - Gentoo wiki](https://wiki.gentoo.org/wiki/GCC_optimization)

