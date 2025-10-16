# etlup

This project contains code for plotting for CMS MTD ETL project. To install you can do,

```bash
pip install etlup
```

Or if you are developing locally you can clone the repo and cd into it. Then do,
```
pip install -U -e ./
```

# Plotting

```python
from etlup.tamalero.Noisewidth import NoisewidthV0
from etlup import now_utc
nw = NoisewidthV0(
    user_created = "hayden",
    location = "CERN",
    measurement_date = now_utc(),
    module = "Module 206",
    pos_0 = [[4, 4, 3, 4, 3, 4, 2, 4, 3, 3, 3, 3, 4, 4, 3, 3,],
            [3, 4, 4, 3, 4, 4, 3, 4, 4, 4, 3, 4, 3, 3, 4, 3,],
            [3, 5, 4, 3, 3, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 4,],
            [3, 3, 3, 3, 4, 3, 4, 3, 4, 3, 3, 3, 4, 3, 3, 3,],
            [3, 4, 3, 3, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3,],
            [3, 4, 4, 3, 4, 3, 3, 3, 3, 4, 3, 3, 3, 3, 4, 4,],
            [3, 4, 4, 4, 3, 3, 4, 4, 4, 5, 4, 4, 4, 4, 4, 3,],
            [3, 3, 3, 3, 2, 4, 3, 3, 4, 4, 3, 3, 4, 3, 3, 4,],
            [3, 4, 4, 4, 4, 3, 3, 4, 5, 3, 4, 3, 3, 4, 3, 3,],
            [4, 3, 3, 3, 3, 4, 4, 3, 3, 4, 4, 3, 3, 3, 4, 4,],
            [4, 4, 4, 4, 3, 4, 3, 4, 4, 4, 3, 3, 4, 3, 3, 4,],
            [3, 3, 4, 3, 3, 3, 3, 3, 3, 4, 3, 4, 4, 3, 3, 3,],
            [4, 3, 4, 3, 4, 3, 4, 3, 3, 3, 4, 3, 3, 4, 3, 3,],
            [3, 4, 5, 4, 3, 4, 3, 3, 4, 4, 3, 4, 3, 4, 3, 4,],
            [3, 3, 4, 4, 3, 4, 3, 4, 4, 3, 4, 3, 4, 3, 4, 3,],
            [4, 3, 3, 3, 3, 3, 3, 4, 4, 3, 3, 4, 3, 4, 3, 3,]]
    # there are the other three positions you can also give
    # pos_1, pos_2, pos_3
)
fig = nw.plot()
fig.savefig("noisewidth.png")
```

# Uploading to Database
In order for you to upload to the database you will need to create a `.env` file in the same directory as the script or pass in its path to the `Session`. Here is an example of a `.env` file:

```
API_TOKEN_ENV = "your token goes here"
```

To upload,
```
from etlup.tamalero.Noisewidth import NoisewidthV0
from etlup import prod_session

tests = [
    NoisewidthV0(...),
    ...
]

prod_session.add_all(tests)
prod_session.upload()
```