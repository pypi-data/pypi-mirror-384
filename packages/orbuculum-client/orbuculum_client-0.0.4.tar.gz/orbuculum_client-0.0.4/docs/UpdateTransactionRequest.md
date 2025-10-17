# UpdateTransactionRequest

Request body for updating an existing transaction

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_id** | **int** | Workspace ID | 
**id** | **int** | Transaction ID to update | 
**sender_account_id** | **int** | Sender account ID | [optional] 
**receiver_account_id** | **int** | Receiver account ID | [optional] 
**sender_amount** | **str** | Sender amount | [optional] 
**receiver_amount** | **str** | Receiver amount | [optional] 
**dt** | **str** | Transaction date and time | [optional] 
**comment** | **str** | Transaction comment | [optional] 
**description** | **str** | Transaction description | [optional] 
**project_id** | **int** | Project ID | [optional] 
**done** | **str** | Transaction status (true/false) | [optional] 

## Example

```python
from orbuculum_client.models.update_transaction_request import UpdateTransactionRequest

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateTransactionRequest from a JSON string
update_transaction_request_instance = UpdateTransactionRequest.from_json(json)
# print the JSON string representation of the object
print(UpdateTransactionRequest.to_json())

# convert the object into a dict
update_transaction_request_dict = update_transaction_request_instance.to_dict()
# create an instance of UpdateTransactionRequest from a dict
update_transaction_request_from_dict = UpdateTransactionRequest.from_dict(update_transaction_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


