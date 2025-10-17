# Netztransparenz Client
This is a small python client to access the data of the german [Netztransparenz portal](https://www.netztransparenz.de/).
It handles authentication, loads the CSV data and transforms it into a [pandas](https://github.com/pandas-dev/pandas) dataframe with some optional format changes.

This is an unofficial client, the makers of this library are not affiliated with NETZTRANSPARENZ.DE.

## Installation
Install from Pypi with 'pip install netztransparenz"

## Example
To use the Netztransparenz API one has to create a free account, see [https://api-portal.netztransparenz.de/](https://api-portal.netztransparenz.de/).
With the account you get the credentials that are needed in the next step.

### Basic usage
```
>>> import netztransparenz as nt
>>> client = nt.NetztransparenzClient("YOUR_CLIENT_ID", "YOUR_CLIENT_SECRET")

#optional: check API status 
>>> client.check_health()
'"OK"'

#load data
>>> df = client.hochrechnung_solar()
>>> df
             Datum    von Zeitzone von    bis Zeitzone bis  50Hertz (MW)  Amprion (MW)  TenneT TSO (MW)  TransnetBW (MW)
0       2011-03-31  22:00          UTC  22:15          UTC          0.00         0.000            0.000            0.000
1       2011-03-31  22:15          UTC  22:30          UTC          0.00         0.000            0.000            0.000
2       2011-03-31  22:30          UTC  22:45          UTC          0.00         0.000            0.000            0.000
...            ...    ...          ...    ...          ...           ...           ...              ...              ...
504046  2025-08-15  09:30          UTC  09:45          UTC       3520.94      7021.757        11195.645         3895.891
504047  2025-08-15  09:45          UTC  10:00          UTC       3597.52      7297.191              NaN         3968.924
504048  2025-08-15  10:00          UTC  10:15          UTC           NaN           NaN              NaN              NaN
```

### Specify timeframe
You can specify the timeframe you want data for:
```
>>> import datetime
>>> start = datetime.datetime(2024, 1, 1, 0, 0)
>>> end = datetime.datetime(2025, 1, 1, 0, 0)
>>> client.hochrechnung_solar(start, end)
            Datum    von Zeitzone von    bis Zeitzone bis  50Hertz (MW)  Amprion (MW)  TenneT TSO (MW)  TransnetBW (MW)
0      2024-01-01  00:00          UTC  00:15          UTC           0.0           0.0              0.0              0.0
1      2024-01-01  00:15          UTC  00:30          UTC           0.0           0.0              0.0              0.0
2      2024-01-01  00:30          UTC  00:45          UTC           0.0           0.0              0.0              0.0
...           ...    ...          ...    ...          ...           ...           ...              ...              ...
35133  2024-12-31  23:15          UTC  23:30          UTC           0.0           0.0              0.0              0.0
35134  2024-12-31  23:30          UTC  23:45          UTC           0.0           0.0              0.0              0.0
35135  2024-12-31  23:45          UTC  00:00          UTC           0.0           0.0              0.0              0.0
```

### Transform dates
For some of the datasets, dates are split up into five columns which makes them hard to sort. If you set the transform_dates flag to true they are converted to two timestamps. 
Also, "von" is turned into the index.

```
>>> client.hochrechnung_solar(start, end, transform_dates=True)
                                                bis  50Hertz (MW)  Amprion (MW)  TenneT TSO (MW)  TransnetBW (MW)
von                                                                                                              
2024-01-01 00:00:00+00:00 2024-01-01 00:15:00+00:00           0.0           0.0              0.0              0.0
2024-01-01 00:15:00+00:00 2024-01-01 00:30:00+00:00           0.0           0.0              0.0              0.0
2024-01-01 00:30:00+00:00 2024-01-01 00:45:00+00:00           0.0           0.0              0.0              0.0
...                                             ...           ...           ...              ...              ...
2024-12-31 23:15:00+00:00 2024-12-31 23:30:00+00:00           0.0           0.0              0.0              0.0
2024-12-31 23:30:00+00:00 2024-12-31 23:45:00+00:00           0.0           0.0              0.0              0.0
2024-12-31 23:45:00+00:00 2025-01-01 00:00:00+00:00           0.0           0.0              0.0              0.0
```