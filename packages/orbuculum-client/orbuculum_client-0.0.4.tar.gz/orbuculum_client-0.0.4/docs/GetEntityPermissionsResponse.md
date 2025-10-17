# GetEntityPermissionsResponse

Response containing entity permissions

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | [optional] 
**data** | [**List[EntityPermission]**](EntityPermission.md) | Array of entity permissions | [optional] 

## Example

```python
from orbuculum_client.models.get_entity_permissions_response import GetEntityPermissionsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GetEntityPermissionsResponse from a JSON string
get_entity_permissions_response_instance = GetEntityPermissionsResponse.from_json(json)
# print the JSON string representation of the object
print(GetEntityPermissionsResponse.to_json())

# convert the object into a dict
get_entity_permissions_response_dict = get_entity_permissions_response_instance.to_dict()
# create an instance of GetEntityPermissionsResponse from a dict
get_entity_permissions_response_from_dict = GetEntityPermissionsResponse.from_dict(get_entity_permissions_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


