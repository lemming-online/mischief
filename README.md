# mischief
mischief is the main backend component for the [lemming.online](https://github.com/lemming-online) project.

## requirements
mischief supports only python 3 officially

mischief requires [pipenv](http://docs.pipenv.org/en/latest/basics.html), which we recommend you install using [pipsi](https://github.com/mitsuhiko/pipsi).
```
curl https://raw.githubusercontent.com/mitsuhiko/pipsi/master/get-pipsi.py | python3
pipsi install pew
pipsi install pipenv
```

alternatively:
```
pip3 install pipenv
```

## installation
```
git clone https://github.com/lemming-online/mischief.git
cd mischief
pipenv install --dev
```
#### dependency management
dependencies are managed using [pipenv](http://docs.pipenv.org/en/latest/basics.html#installing-packages-for-your-project).

to completely update the environment:
```
pipenv upgrade --dev
```
## usage

#### running the server
```
pipenv run python run.py
```

#### activate the virtualenv to interact with it
```
pipenv shell
```


#### testing
tests are managed using py.test.
```
pipenv run py.test
```

#### cleaning up
```
pipenv uninstall --all
```


## the lemmings
lemming.online is a project developed for Purdue's CS407 Senior Project class, by seniors jeremy craven, jay hankins, ankit patanaik, and matthew ess.
