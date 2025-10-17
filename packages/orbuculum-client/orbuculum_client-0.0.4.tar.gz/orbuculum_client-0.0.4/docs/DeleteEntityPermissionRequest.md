# DeleteEntityPermissionRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_id** | **int** | Workspace ID | 
**entity_id** | **int** | Entity ID | 
**role_id** | **int** | Role ID | 
**can_manage** | **bool** | Whether to delete manage permission | 

## Example

```python
from orbuculum_client.models.delete_entity_permission_request import DeleteEntityPermissionRequest

# TODO update the JSON string below
json = "{}"
# create an instance of DeleteEntityPermissionRequest from a JSON string
delete_entity_permission_request_instance = DeleteEntityPermissionRequest.from_json(json)
# print the JSON string representation of the object
print(DeleteEntityPermissionRequest.to_json())

# convert the object into a dict
delete_entity_permission_request_dict = delete_entity_permission_request_instance.to_dict()
# create an instance of DeleteEntityPermissionRequest from a dict
delete_entity_permission_request_from_dict = DeleteEntityPermissionRequest.from_dict(delete_entity_permission_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


