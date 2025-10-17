# MyLibrary

## Usage

- clone this repo and `cd mylibrary`
- `pip install -e .`

## Release

```commandline
python setup.py sdist
twine upload dist/wxw-x.x.x.tar.gz --verbose
```