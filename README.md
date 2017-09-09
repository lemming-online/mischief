# mischief
mischief is the main backend component for the [lemming.online](https://github.com/lemming-online) project

## requirements
mischief requires python3 and the virtualenv python package.

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
it is highly recommended to use [requirements-tools](https://github.com/yelp/requirements-tools) to manage adding new dependencies to mischief. add the dependency to one of the `minimal` requirements files, pinned if necessary or unpinned for latest, and run `$ upgrade-requirements` to generate a new `requirements.txt` file.


## the lemmings
lemming.online is a project developed for Purdue's CS407 Senior Project class, by seniors jeremy craven, jay hankins, ankit patanaik, and matthew ess.

