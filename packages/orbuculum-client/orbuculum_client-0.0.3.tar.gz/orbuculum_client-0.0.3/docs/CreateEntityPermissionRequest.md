# CreateEntityPermissionRequest

Request body for creating entity permission

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_id** | **int** | Workspace ID | 
**entity_id** | **int** | Entity ID | 
**role_id** | **int** | Role ID | 
**can_manage** | **bool** | Management permission (default: false) | [optional] 

## Example

```python
from orbuculum_client.models.create_entity_permission_request import CreateEntityPermissionRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateEntityPermissionRequest from a JSON string
create_entity_permission_request_instance = CreateEntityPermissionRequest.from_json(json)
# print the JSON string representation of the object
print(CreateEntityPermissionRequest.to_json())

# convert the object into a dict
create_entity_permission_request_dict = create_entity_permission_request_instance.to_dict()
# create an instance of CreateEntityPermissionRequest from a dict
create_entity_permission_request_from_dict = CreateEntityPermissionRequest.from_dict(create_entity_permission_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


