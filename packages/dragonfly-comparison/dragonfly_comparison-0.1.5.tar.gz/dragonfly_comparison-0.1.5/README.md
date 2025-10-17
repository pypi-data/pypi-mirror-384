![Dragonfly](https://www.ladybug.tools/assets/img/dragonfly.png)

[![Build Status](https://github.com/ladybug-tools/dragonfly-comparison/actions/workflows/ci.yaml/badge.svg)](https://github.com/ladybug-tools/dragonfly-comparison/actions)

[![Python 3.10](https://img.shields.io/badge/python-3.10-orange.svg)](https://www.python.org/downloads/release/python-3100/) [![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/) [![Python 2.7](https://img.shields.io/badge/python-2.7-green.svg)](https://www.python.org/downloads/release/python-270/) [![IronPython](https://img.shields.io/badge/ironpython-2.7-red.svg)](https://github.com/IronLanguages/ironpython2/releases/tag/ipy-2.7.8/)

# dragonfly-comparison

Dragonfly extension for comparing dragonfly models with one another.

## Installation

`pip install dragonfly-comparison`

## QuickStart

```python
import dragonfly_comparison
```

## [API Documentation](http://ladybug-tools.github.io/dragonfly-comparison/docs)

## Local Development

1. Clone this repo locally
```
git clone git@github.com:ladybug-tools/dragonfly-comparison

# or

git clone https://github.com/ladybug-tools/dragonfly-comparison
```
2. Install dependencies:
```
cd dragonfly-comparison
pip install -r dev-requirements.txt
pip install -r requirements.txt
```

3. Run Tests:
```
python -m pytest tests/
```

4. Generate Documentation:
```
sphinx-apidoc -f -e -d 4 -o ./docs ./dragonfly_comparison
sphinx-build -b html ./docs ./docs/_build/docs
```
