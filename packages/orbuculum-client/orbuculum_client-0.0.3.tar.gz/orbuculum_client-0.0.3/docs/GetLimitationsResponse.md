# GetLimitationsResponse

Response containing limitation data

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | [optional] 
**data** | [**List[Limitation]**](Limitation.md) | Array of limitations | [optional] 
**total** | **int** | Total number of limitations | [optional] 

## Example

```python
from orbuculum_client.models.get_limitations_response import GetLimitationsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GetLimitationsResponse from a JSON string
get_limitations_response_instance = GetLimitationsResponse.from_json(json)
# print the JSON string representation of the object
print(GetLimitationsResponse.to_json())

# convert the object into a dict
get_limitations_response_dict = get_limitations_response_instance.to_dict()
# create an instance of GetLimitationsResponse from a dict
get_limitations_response_from_dict = GetLimitationsResponse.from_dict(get_limitations_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


