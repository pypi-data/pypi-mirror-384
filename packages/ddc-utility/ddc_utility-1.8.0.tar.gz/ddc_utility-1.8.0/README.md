# DDC Utility

This is the Danube Data Cube Utility library, for interacting with the DDC API service.

### Installation

```bash
pip install ddc-utility
```

### Usage

Users must have a valid DDC registration.

### Example #1 (using DdcClient with client ID and secret)
This example walks you through the process of creating and opening an AOI cube.

```
$ python

# Importing packages
>>> import os
>>> from ddc_utility.client import DdcClient

# Setting DDC credentials
>>> os.environ['DDC_CLIENT_ID'] = "<client id>"
>>> os.environ['DDC_CLIENT_SECRET'] = "<client secret>"

# Initialize DDC client 
>>> client = DdcClient()

# List available data layers
>>> client.get_data_layers()

# List user's AOIs
>>> client.get_all_aoi()

# Create an AOI
>>>  res = client.create_aoi(name="My AOI",
                  geometry="POLYGON ((19.021454 47.507925, 19.043941 47.489601, 19.047031 47.490181, 19.039478 47.506997, 19.021454 47.507925))",
                  time_range=("2023-06-01", "2023-07-01"),
                  layer_ids=[4, 8, 15, 48])
>>> id = res.iloc[0]['id']
                  
# Check if AOI is 'ready'
>>> info = client.get_aoi_by_id(id)
>>> print(f"AOI status is: {info.iloc[0]['status']}")

# If status is 'ready', open cube
>>> ds = client.open_aoi_cube(aoi_id=id)

```

### Example #2 (using IntegrationClient with bearer token)
This example shows how you can retrieve the dataset associated with a growing season if you have a valid OAuth2 bearer token.

```
$ python

# Importing packages
>>> from ddc_utility.client import IntegrationClient

# Initialize Integration client 
>>> client = IntegrationClient(
    bearer_token="...",
    expires_in=86400,
)

# Retrieve xarray Dataset for the specified growing season
>>> ds = client.open_growing_season_cube(1234)

```
