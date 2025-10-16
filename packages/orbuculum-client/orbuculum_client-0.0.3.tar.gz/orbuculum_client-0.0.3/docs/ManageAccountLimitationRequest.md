# ManageAccountLimitationRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_id** | **int** | Workspace ID | 
**account_id** | **int** | Account ID | 
**action** | **str** | Action to perform | 
**type** | **str** | Limitation type | [optional] 
**value** | **float** | Limitation value | [optional] 
**currency** | **str** | Currency code | [optional] 
**period** | **str** | Time period | [optional] 
**limitation_id** | **int** | Limitation ID (for update/delete) | [optional] 

## Example

```python
from orbuculum_client.models.manage_account_limitation_request import ManageAccountLimitationRequest

# TODO update the JSON string below
json = "{}"
# create an instance of ManageAccountLimitationRequest from a JSON string
manage_account_limitation_request_instance = ManageAccountLimitationRequest.from_json(json)
# print the JSON string representation of the object
print(ManageAccountLimitationRequest.to_json())

# convert the object into a dict
manage_account_limitation_request_dict = manage_account_limitation_request_instance.to_dict()
# create an instance of ManageAccountLimitationRequest from a dict
manage_account_limitation_request_from_dict = ManageAccountLimitationRequest.from_dict(manage_account_limitation_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


