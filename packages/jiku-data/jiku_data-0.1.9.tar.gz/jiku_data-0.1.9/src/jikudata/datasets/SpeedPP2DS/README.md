# SpeedPP2D



2D plantar pressure *time series* (3D) data from Pataky et al. (2008).

Made public by agreement by authors Pataky and Crompton on 2024-05-27.

<br>

<br>

**Dataset overview**

- Task:
  - 10 participants
  - Walking at three speeds: Slow, Normal and Fast 
  - Speed conditions encoded as 1=Slow, 2=Normal, 3=Fast
  - 20 repetititions each condition
  - 60 total trials per participant
  - 600 total trials
- Measurements:
  - Walking speed (average progression-direction speed of a single reflective marker attached to subject's torso)
  - 2D plantar pressure distribution time series (3D arrays) recorded at 500 Hz

<br>

<br>

**Dependent variable shape**

After loading the data you will see that the dependent variable `y` is a 4D array:

```python
dataset   = jd.SpeedPP2DS()
print( dataset.y.shape )   # (600,66,33,500) array
```

The four dimensions are:

- axis 0:  trial
- axis 1:  spatial x direction (progression direction)
- axis 2:  spatial y direction (mediolateral direction)
- axis 3:  time

<br>

<br>

**Loading entire dataset**

The entire dataset (all 600 trials) can be loaded using:

```python
dataset   = jikudata.SpeedPP2DS()
print( dataset.y.shape )   # (600,66,33,500) array
```

However, the dataset is large:  a `(600,66,33,500)` 4D array, so it takes a long time to load. For quicker loading, and/or when only a single participant's data are required, see the section below. 

<br>

<br>

**Loading a single participant's data**

A single participant's data can be loaded using the `subj` keyword argument along with an integer between `0` and `9` :

```python
dataset   = jikudata.SpeedPP2DS( subj=0 )
print( dataset.y.shape )  # (60,66,33,500) array
```

This yields a  `(60,66,33,500)` 4D array.

<br>

<br>

**Unpadding time axis**

There are 500 time frames representing one second of data (sampling rate = 500 Hz). The longest contact duration is approximately 440 frames, but all measurements were zero-padded to 500 frames so that the data can be loaded as a single 4D array. 

An individual observation can be unpadded using the `unpad3` utility function like this:

```python
import jikudata
from jikudata.util.array import unpad3

dataset   = jikudata.SpeedPP2DS( subj=0 )
y         = dataset.y[0]  # first observation, zero-padded to 500 time frames
yu        = unpad3( y )   # unpadded observation

print( y.shape )   # (63, 33, 500)
print( yu.shape )  # (63, 33, 266)
```

<br>

<br>

**Reference**

Pataky, T. C., Caravaggi, P., Savage, R., Parker, D., Goulermas, J., Sellers, W., & Crompton, R. (2008). New insights into the plantar pressure correlates of walking speed using pedobarographic statistical parametric mapping (pSPM). Journal of Biomechanics, 41(9), 1987–1994.

https://doi.org/10.1016/j.jbiomech.2008.03.034
