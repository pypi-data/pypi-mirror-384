# Account

Account object with all details

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** | Account ID | [optional] 
**name** | **str** | Account name | [optional] 
**entity_id** | **int** | Entity ID | [optional] 
**currency_id** | **int** | Currency ID | [optional] 
**hidden** | **bool** | Whether the account is hidden | [optional] 
**hide_balances** | **bool** | Whether balances are hidden | [optional] 
**api_id** | **int** | API ID | [optional] 
**commission_type** | **int** | Commission type (1 for enabled, any other value for disabled) | [optional] 
**commission_account_id** | **int** | Commission account ID | [optional] 
**commission_value** | **float** | Commission value | [optional] 
**created_at** | **datetime** | Creation timestamp | [optional] 
**updated_at** | **datetime** | Update timestamp | [optional] 
**custom_commission_sender_id** | **int** | Custom commission sender ID | [optional] 
**commission_appliance** | **int** | Commission appliance (0 or 1) | [optional] 
**limited** | **bool** | Whether the account is limited | [optional] 

## Example

```python
from orbuculum_client.models.account import Account

# TODO update the JSON string below
json = "{}"
# create an instance of Account from a JSON string
account_instance = Account.from_json(json)
# print the JSON string representation of the object
print(Account.to_json())

# convert the object into a dict
account_dict = account_instance.to_dict()
# create an instance of Account from a dict
account_from_dict = Account.from_dict(account_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


