# T96 Parameters Downloader

This script downloads **1 hour interval** data from **omni2** spacecraft (dataset) from [OmniWeb](https://omniweb.gsfc.nasa.gov/). Data is valid for interval **1.1.1968** untill **newest available data**.

## Requirements

To run the script you need [Python](https://www.python.org/) and [pip](https://pypi.org/project/pip/) installed. This script was developed with **Python 3.10.6**, but it might work with earlier versions. To install the required packages just run `pip3 install -r requirements.txt`.


## Run instructions

If you have all the requirements, you just need to run `python3 ./pull_parmod.py`

## Output file description

The script creates the following files in the current directory when run:

1. `parmod_new_intermediate.dat` this file contains intermediate products straight from [OmniWeb](https://omniweb.gsfc.nasa.gov/). Missing values are indicated by value *999.9* in the case of the intensity of `y` and `z` components of the interplanetary field, *99.99* in the case of `pdyn`, and *99999* in the case of `Dst` index. This file contains the following columns:

	1. `year` specifying the year;
	2. `month` specifying the month;
	3. `day` specifying the day;
	4. `hour` specifying the hour;
	5. `doy` specifying the Day of Year;
	6. `By` intensity of `y` component of the interplanetary field;
	7. `Bz` intensity of `z` component of the interplanetary field;
	8. `pdyn` dynamic pressure of solar wind (in `nPa`) at a given date and time;
	9. `Dst` index (in `nT`).

2. `parmod_new_interp.dat` this file contains linearly interpolated intermediate data with an indication of which values were missing. The file format is the same as in the `parmod_new_intermediate.dat` with an additional column that contains an `ASCII` encoded decimal value which is the result of bitwise **or** (or numerical add) operation of values representing missing columns before interpolation where the following values have the following meaning:

	- `0000 0100` (4) - a value of `By` was missing and the current value in the appropriate column was computed by linear interpolation;
	- `0000 1000` (8) - the value of  `Bz` was missing and the current value in the appropriate column was computed by linear interpolation;
	- `0000 0010` (2) - the value of  `pdyn` was missing and the current value in the appropriate column was computed by linear interpolation;
	- `0001 0000` (16) - the value of  `Dst` was missing and the current value in the appropriate column was computed by linear interpolation.
