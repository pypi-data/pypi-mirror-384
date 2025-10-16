# LimitationManagedResponse

Response after managing account or entity limitation

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | [optional] 
**message** | **str** | Success message | [optional] 
**limitation_id** | **int** | Limitation ID | [optional] 

## Example

```python
from orbuculum_client.models.limitation_managed_response import LimitationManagedResponse

# TODO update the JSON string below
json = "{}"
# create an instance of LimitationManagedResponse from a JSON string
limitation_managed_response_instance = LimitationManagedResponse.from_json(json)
# print the JSON string representation of the object
print(LimitationManagedResponse.to_json())

# convert the object into a dict
limitation_managed_response_dict = limitation_managed_response_instance.to_dict()
# create an instance of LimitationManagedResponse from a dict
limitation_managed_response_from_dict = LimitationManagedResponse.from_dict(limitation_managed_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


