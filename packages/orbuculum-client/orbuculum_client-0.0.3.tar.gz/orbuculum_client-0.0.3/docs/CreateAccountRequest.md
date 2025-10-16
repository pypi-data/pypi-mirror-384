# CreateAccountRequest

Request body for creating a new account

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_id** | **int** | Workspace ID | 
**entity_id** | **int** | Entity ID | 
**name** | **str** | Account name | 
**currency_id** | **int** | Currency ID | [optional] 
**hidden** | **str** | Whether account is hidden (0 or 1) | [optional] 
**hide_balances** | **str** | Whether balances are hidden (0 or 1) | [optional] 
**commission_enabled** | **str** | Whether commission is enabled (0 or 1) | [optional] 
**commission_appliance** | **int** | Commission appliance type | [optional] 
**commission_sender_account** | **int** | Commission sender account ID | [optional] 
**commission_receiver_account** | **int** | Commission receiver account ID | [optional] 
**api_id** | **str** | External API ID | [optional] 
**type** | **str** | Account type | [optional] 

## Example

```python
from orbuculum_client.models.create_account_request import CreateAccountRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateAccountRequest from a JSON string
create_account_request_instance = CreateAccountRequest.from_json(json)
# print the JSON string representation of the object
print(CreateAccountRequest.to_json())

# convert the object into a dict
create_account_request_dict = create_account_request_instance.to_dict()
# create an instance of CreateAccountRequest from a dict
create_account_request_from_dict = CreateAccountRequest.from_dict(create_account_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


