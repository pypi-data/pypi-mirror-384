# tagmapper-sdk [![SNYK dependency check](https://github.com/equinor/tagmapper-sdk/actions/workflows/snyk.yml/badge.svg)](https://github.com/equinor/tagmapper-sdk/actions/workflows/snyk.yml)
Python package to get timeseries and constant value mappings for data models from SDP tag mapping library.

It supports SDP defined models for Separators and Wells as well as generic models with or without schema.

Authentication is done using Azure credentials and bearer tokens.


## Use
1. See [demo](examples/demo_well.py). Or try the following simple code.  
    ```python
    from tagmapper import Well
    w = Well("NO 30/6-E-2")  
    ```

2. Fetching the base view (well_attributes_mapped_to_timeseries_base) from the API: <br>
    Refer to examples/demo_api_func.py:<br>
    Fetch data for all facilities:<br>
    ```python
    from tagmapper.base_model import get_data_base_well
    df = get_data_base_well(limit=100000, offset=0) 
    print(df)
    ```
    Fetch data for selected facilities:
    ```python
    from tagmapper.base_model import get_data_base_well
    facility_names = ['STATFJORD B','JOHAN SVERDRUP RP']
    df = get_data_base_well(facility_names, limit=10000, offset=0) # More facilit
    print(df)
    ```

3. Getting a generic model with no schema from API:  
   See [demo](examples/demo_generic_model.py). Example usage:
     ```python
     from tagmapper import Model

     # Create a model
     model = Model.get_model(
     model_owner="example_owner",
     model_name="example_model",
     object_name="example_object")
     model.print_report()
     ```

## Installing
Install from pypi using pip.  
``
pip install tagmapper
``


## Developing
Clone repo and run ``poetry install`` to install dependencies.


## Testing
Run tests and check coverage using pytest-cov
``poetry run pytest --cov=tagmapper test/ --cov-report html``
