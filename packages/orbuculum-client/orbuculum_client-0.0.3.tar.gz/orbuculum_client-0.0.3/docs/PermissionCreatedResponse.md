# PermissionCreatedResponse

Response after creating permission

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | [optional] 
**id** | **int** | Created permission ID | [optional] 
**message** | **str** | Success message | [optional] 

## Example

```python
from orbuculum_client.models.permission_created_response import PermissionCreatedResponse

# TODO update the JSON string below
json = "{}"
# create an instance of PermissionCreatedResponse from a JSON string
permission_created_response_instance = PermissionCreatedResponse.from_json(json)
# print the JSON string representation of the object
print(PermissionCreatedResponse.to_json())

# convert the object into a dict
permission_created_response_dict = permission_created_response_instance.to_dict()
# create an instance of PermissionCreatedResponse from a dict
permission_created_response_from_dict = PermissionCreatedResponse.from_dict(permission_created_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


