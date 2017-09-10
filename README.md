# mischief
mischief is the main backend component for the [lemming.online](https://github.com/lemming-online) project

## requirements
mischief requires [pipenv](http://docs.pipenv.org/en/latest/basics.html), which should be installed using [pip](https://pip.pypa.io/en/stable/installing/).

## installation
```
$ git clone https://github.com/lemming-online/mischief.git
$ cd mischief
$ make
$ source venv/bin/activate
```
to run the development server:
```
$ make run
```

#### dependency management
dependencies are managed by [pipenv](http://docs.pipenv.org/en/latest/basics.html#installing-packages-for-your-project), which can be used directly (rather than through the Makefile) to manipulate dependencies.

## the lemmings
lemming.online is a project developed for Purdue's CS407 Senior Project class, by seniors jeremy craven, jay hankins, ankit patanaik, and matthew ess.

