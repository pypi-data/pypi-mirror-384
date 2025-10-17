# Limitation

Limitation object with all details

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** | Limitation ID | [optional] 
**type** | **str** | Limitation type | [optional] 
**value** | **float** | Limitation value | [optional] 
**currency** | **str** | Currency code | [optional] 
**period** | **str** | Time period | [optional] 
**active** | **bool** | Whether limitation is active | [optional] 

## Example

```python
from orbuculum_client.models.limitation import Limitation

# TODO update the JSON string below
json = "{}"
# create an instance of Limitation from a JSON string
limitation_instance = Limitation.from_json(json)
# print the JSON string representation of the object
print(Limitation.to_json())

# convert the object into a dict
limitation_dict = limitation_instance.to_dict()
# create an instance of Limitation from a dict
limitation_from_dict = Limitation.from_dict(limitation_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


