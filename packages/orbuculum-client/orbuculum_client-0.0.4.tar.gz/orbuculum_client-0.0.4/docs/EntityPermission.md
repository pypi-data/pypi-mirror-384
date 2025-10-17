# EntityPermission

Entity permission object

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**entity_id** | **int** | Entity ID | [optional] 
**entity_name** | **str** | Entity name | [optional] 
**can_read** | **bool** | Read permission | [optional] 
**can_write** | **bool** | Write permission | [optional] 
**can_delete** | **bool** | Delete permission | [optional] 

## Example

```python
from orbuculum_client.models.entity_permission import EntityPermission

# TODO update the JSON string below
json = "{}"
# create an instance of EntityPermission from a JSON string
entity_permission_instance = EntityPermission.from_json(json)
# print the JSON string representation of the object
print(EntityPermission.to_json())

# convert the object into a dict
entity_permission_dict = entity_permission_instance.to_dict()
# create an instance of EntityPermission from a dict
entity_permission_from_dict = EntityPermission.from_dict(entity_permission_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


