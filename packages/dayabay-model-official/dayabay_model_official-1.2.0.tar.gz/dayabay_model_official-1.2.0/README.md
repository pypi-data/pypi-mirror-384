# dayabay-model-official

[![python](https://img.shields.io/badge/python-3.11-purple.svg)](https://www.python.org/)
[![pipeline](https://git.jinr.ru/dagflow-team/dayabay-model-official/badges/main/pipeline.svg)](https://git.jinr.ru/dagflow-team/dayabay-model-official/commits/main)
[![coverage report](https://git.jinr.ru/dagflow-team/dayabay-model-official/badges/main/coverage.svg)](https://git.jinr.ru/dagflow-team/dayabay-model-official/-/commits/main)

<!--- Uncomment here after adding docs!
[![pages](https://img.shields.io/badge/pages-link-white.svg)](http://dagflow-team.pages.jinr.ru/dayabay-model-official)
-->

Official model of the Daya Bay reactor antineutrino experiment for neutrino oscillation analysis based on gadolinium capture data.

## Repositories

- Development/CI: https://git.jinr.ru/dagflow-team/dayabay-model-official
- Contact/pypi/mirror: https://github.com/dagflow-team/dayabay-model-official
- PYPI: https://pypi.org/project/dayabay-model-official

## Minimal working example

If you want to run examples from `extras/mwe`, clone this repository `git clone https://github.com/dagflow-team/dayabay-model-official` and change position to cloned reposiotry `cd dayabay-model-official`.
However, you can just copy examples that are listed below and run them where you want after installation of package and several others steps:

1. Install package `pip install dayabay-model-official`
2. Clone data repository: `git clone https://github.com/dagflow-team/dayabay-data-official`
3. Create soft link to any data type. For example, to `hdf5`-type: `ln -s dayabay-data-official/hdf5 data/`
4. Run script `extras/mwe/run.py`
```python
from dayabay_model_official import model_dayabay

model = model_dayabay()
print(model.storage["outputs.statistic.full.pull.chi2p"].data)
```
within `python`
```bash
python extras/mwe/run.py
```
5. Check output in console, it might be something like below
```bash
INFO: Model version: model_dayabay
INFO: Source type: npz
INFO: Data path: data
INFO: Concatenation mode: detector_period
INFO: Spectrum correction mode: exponential
INFO: Spectrum correction location: before integration
[0.]
```
6. Also, you may pass custom path to data, if you put `path_data` parameter to model. For example,
```python
from dayabay_model_official import model_dayabay

model = model_dayabay(path_data="dayabay-model-official/npz")
print(model.storage["outputs.statistic.full.pull.chi2p"].data)
```
Example can be executed: `python extras/mwe/run-custom-data-path.py`

7. If you want to switch between Asimonv and observed data, you need to switch input in the next way
```python
from dayabay_model_official import model_dayabay

model = model_dayabay(path_data="dayabay-model-official/npz")

print(model.storage["outputs.statistic.full.pull.chi2p"].data)

model.switch_data("real")
print(model.storage["outputs.statistic.full.pull.chi2p"].data)

model.switch_data("asimov")
print(model.storage["outputs.statistic.full.pull.chi2p"].data)
```
Example can be executed: `python extras/mwe/run-switch-asimov-real-data.py`
