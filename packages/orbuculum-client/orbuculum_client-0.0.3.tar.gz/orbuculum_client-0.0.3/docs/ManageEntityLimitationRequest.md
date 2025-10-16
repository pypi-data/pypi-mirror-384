# ManageEntityLimitationRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_id** | **int** | Workspace ID | 
**target_account_id** | **int** | Target account ID | 
**limitation_entity_id** | **int** | Limitation entity ID | 
**limitation** | **str** | Limitation value | 
**project_id** | **int** | Project ID | 

## Example

```python
from orbuculum_client.models.manage_entity_limitation_request import ManageEntityLimitationRequest

# TODO update the JSON string below
json = "{}"
# create an instance of ManageEntityLimitationRequest from a JSON string
manage_entity_limitation_request_instance = ManageEntityLimitationRequest.from_json(json)
# print the JSON string representation of the object
print(ManageEntityLimitationRequest.to_json())

# convert the object into a dict
manage_entity_limitation_request_dict = manage_entity_limitation_request_instance.to_dict()
# create an instance of ManageEntityLimitationRequest from a dict
manage_entity_limitation_request_from_dict = ManageEntityLimitationRequest.from_dict(manage_entity_limitation_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


