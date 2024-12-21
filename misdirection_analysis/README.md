## Data File (`data.py`)

- Ensure that the directory `data/parqs` exists.

- Use `load_tracking_raw(gid: int) -> pd.DataFrame` to load the raw tracking data by game ID. Will take about 30 seconds to run for the first time as it caches all the tracking data for all games and weeks.

- Use `load_tracking_adjusted(gid: int) -> pd.DataFrame` to load the adjusted tracking data by game ID. Will take a few minutes to run for the first time as it computes and caches all the adjusted tracking data for all games and weeks.

The adjusted tracking data does not include `s`, `a`, `o`, or `dir`, but instead includes acceleration and velocity vectors. The `x` and `y` coordinates have also been adjusted to be relative to the line of scrimmage and the football's position (`x` and `y` are also swapped so `x` has a range of `53` and `y` a range of `120`). View the graphic below for intuition on how the data has been adjusted.

![graphic](graphics/graphic.png)
