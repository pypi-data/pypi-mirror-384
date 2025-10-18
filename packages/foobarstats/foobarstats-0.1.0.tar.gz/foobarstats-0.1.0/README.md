# FoobarStats

[![PyPI version](https://img.shields.io/pypi/v/foobarstats)](https://pypi.org/project/foobarstats/ )
[![License](https://img.shields.io/github/license/Olezhich/FoobarStats)](https://github.com/Olezhich/FoobarStats/blob/main/LICENSE )
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)  
[![Coverage Status](https://coveralls.io/repos/github/Olezhich/FoobarStats/badge.svg?branch=dev)](https://coveralls.io/github/Olezhich/FoobarStats?branch=dev)
[![Build Status](https://github.com/Olezhich/FoobarStats/workflows/Run%20Tests%20on%20PR/badge.svg )](https://github.com/Olezhich/FoobarStats/actions )


> A lightweight library for parsing foobar2000 XML statistics into Pydantic models

## Features

- Parsing `Foobar2000` XML statistics files
- Using `Pydantic`
- Simple and intuitive API
- Using generators to reduce memory consumption
- Supports Python 3.10+

## QuickStart

### Foobar2000 XML export

First, select the tracks in the playlist for which you want to export statistics > right-click > Playback Statistics > Export Statistics to XML...

Then a window will appear:

![export window view](export.png)

### Instalation of the library
#### Via pip
```commandline
pip install foobarstats
```
#### Via poetry
```commandline
poetry add commandline
```
### Using of the library
```python
import foobarstats

with open('your_filepath.xml', 'r') as fp:
    for stat in foobarstats.load(fp):
        print(stat) # prints TrackStat object
```

