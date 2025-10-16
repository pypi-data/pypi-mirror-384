# sports-features

<a href="https://pypi.org/project/sportsfeatures/">
    <img alt="PyPi" src="https://img.shields.io/pypi/v/sportsfeatures">
</a>

A library for processing sports features over a dataframe containing sports data.

## Dependencies :globe_with_meridians:

Python 3.11.6:

- [openskill](https://openskill.me/en/latest/index.html)
- [pandas](https://pandas.pydata.org/)
- [feature-engine](https://feature-engine.trainindata.com/en/latest/)
- [tqdm](https://github.com/tqdm/tqdm)
- [scikit-learn](https://scikit-learn.org/)
- [geopy](https://geopy.readthedocs.io/en/stable/)
- [numpy](https://numpy.org/)
- [pytest-is-running](https://github.com/adamchainz/pytest-is-running)
- [joblib](https://joblib.readthedocs.io/en/stable/)
- [timeseries-features](https://github.com/8W9aG/timeseries-features)
- [textfeats](https://github.com/8W9aG/text-features)
- [scipy](https://scipy.org/)
- [image-features](https://github.com/8W9aG/image-features)
- [requests-cache](https://requests-cache.readthedocs.io/en/stable/)

## Raison D'être :thought_balloon:

`sportsfeatures` aims to process features relevant to predicting aspects of sporting games.

## Architecture :triangular_ruler:

`sportsfeatures` is a functional library, meaning that each phase of feature extraction gets put through a different function until the final output. It contains some caching when the processing is heavy (such as skill processing). The features its computes are as follows:

1. Process the player and teams skill levels using [OpenSkill](https://openskill.me/en/latest/index.html). This is an ELO like rating system giving a probability of win and loss.
2. Compute the offensive efficiency of each team/player.
3. Compute the time series values of the numeric features for each team/player over the various windows provided. This includes lag, count, sum, mean, median, var, std, min, max, skew, kurt, sem, rank.
4. Compute the datetime features for any datetime columns.
5. Remove the lookahead features.

## Installation :inbox_tray:

This is a python package hosted on pypi, so to install simply run the following command:

`pip install sportsfeatures`

or install using this local repository:

`python setup.py install --old-and-unmanageable`

## Usage example :eyes:

The use of `sportsfeatures` is entirely through code due to it being a library. It attempts to hide most of its complexity from the user, so it only has a few functions of relevance in its outward API.

### Generating Features

To generate features:

```python
import datetime

import pandas as pd

from sportsfeatures.process import process
from sportsfeatures.identifier import Identifier
from sportsfeatures.entity_type import EntityType

df = ... # Your sports data
identifiers = [
    Identifier(EntityType.TEAM, "teams/0/id", ["teams/0/kicks"], "teams/0"),
    Identifier(EntityType.TEAM, "teams/1/id", ["teams/1/kicks"], "teams/1"),
]
df = process(df, identifiers, [datetime.timedelta(days=365), None], "dt")
```

This will produce a dataframe that contains the new sports related features.

## License :memo:

The project is available under the [MIT License](LICENSE).
