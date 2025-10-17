[![Upload Python Package](https://github.com/GrafLearnt/pstats_extender/actions/workflows/python-publish.yml/badge.svg)](https://github.com/GrafLearnt/pstats_extender/actions/workflows/python-publish.yml) ![PyPI version](https://badge.fury.io/py/pstats_extender.svg) ![Python Versions](https://img.shields.io/pypi/pyversions/pstats_extender.svg) [![pstats-extender](https://snyk.io/advisor/python/pstats-extender/badge.svg)](/advisor/python/pstats-extender)
# Abstract
Designed to save pstats log to folder...
# Install
```bash
    pip3 install pstats_extender
```
# Usage
```python
import pstats_extender


@pstats_extender.profile()
def some_function():
    ...
```
## or
```python
import pstats_extender


with pstats_extender.profile(
    sortby=pstats_extenter.SortKey.CUMULATIVE, directory="../pstats"
):
    # your code here
```
## or
```python
import pstats_extender


with pstats_extender.profile():
    # your code here
```


## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.
