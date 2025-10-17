# UpdateAccountRequest

Request body for updating an existing account

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_id** | **int** | Workspace ID | 
**id** | **int** | Account ID to update | 
**name** | **str** | New account name | [optional] 
**currency_id** | **int** | Currency ID | [optional] 
**commission_type** | **str** | Commission type | [optional] 
**commission_value** | **float** | Commission value | [optional] 
**hidden** | **bool** | Whether account is hidden | [optional] 

## Example

```python
from orbuculum_client.models.update_account_request import UpdateAccountRequest

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateAccountRequest from a JSON string
update_account_request_instance = UpdateAccountRequest.from_json(json)
# print the JSON string representation of the object
print(UpdateAccountRequest.to_json())

# convert the object into a dict
update_account_request_dict = update_account_request_instance.to_dict()
# create an instance of UpdateAccountRequest from a dict
update_account_request_from_dict = UpdateAccountRequest.from_dict(update_account_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


