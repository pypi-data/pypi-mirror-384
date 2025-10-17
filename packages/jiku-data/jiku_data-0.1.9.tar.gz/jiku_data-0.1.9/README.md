[![Python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://www.python.org)
[![Numpy](https://img.shields.io/badge/Numpy-777BB4?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
![version](https://img.shields.io/badge/version-0.1.9-blue)



<img src="https://github.com/jiku-pro/jiku-data/blob/ee4a7ccc53b7badedc14d7c93b2b40af783b4f75/jiku-core.jpg?raw=true" alt="JikuCore" width="600">

# JIKU DATA

Public repository of open-source datasets, and a component of the [Jiku Core](https://jiku-core.org) software suite.



Datasets appear in `./src/jikudata/datasets` and are all sourced from the internet, academic papers and open databases. Dataset-specific licenses are provided where required.



Example use:

```python
import jikudata as jd

dataset = jd.RSRegression()
y       = dataset.y  # dependent variable
x       = dataset.x  # independent variable(s)

print( dataset )
print( dataset.www )


```

Output:

```
RSRegression:
    design : Linear regression
    dim    : 0
    y      : (15,) array
    expected : 
        ExpectedResultsSPM1D:
            STAT : T
            z    : -3.67092
            df   : (1, 13)
            p    : 0.0028
            
https://www.real-statistics.com/regression/hypothesis-testing-significance-regression-line-slope/
```





Iterate through all datasets:

```python
for dataset in jd.datasets.iter_all():
		print( dataset.name )
```

