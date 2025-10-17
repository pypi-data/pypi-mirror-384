# Transaction

Transaction details

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** | Transaction ID | [optional] 
**workspace_id** | **int** | Workspace ID | [optional] 
**dt** | **str** | Transaction date and time | [optional] 
**comment** | **str** | Transaction comment | [optional] 
**description** | **str** | Transaction description | [optional] 
**sender_account_id** | **int** | Sender account ID | [optional] 
**sender_amount** | **str** | Sender amount | [optional] 
**sender_balance_after** | **str** | Sender balance after transaction | [optional] 
**receiver_account_id** | **int** | Receiver account ID | [optional] 
**receiver_amount** | **str** | Receiver amount | [optional] 
**receiver_balance_after** | **str** | Receiver balance after transaction | [optional] 
**project_id** | **int** | Project ID | [optional] 
**commission_applied** | **bool** | Whether commission was applied | [optional] 
**chained_receiver_commission** | **int** | Chained receiver commission transaction ID | [optional] 
**chained_id** | **int** | Chained transaction ID | [optional] 
**chained_commission_id** | **int** | Chained commission transaction ID | [optional] 
**done** | **bool** | Transaction completion status | [optional] 
**apikey** | **str** | API key for external integrations | [optional] 
**future_id** | **int** | Future transaction ID | [optional] 
**future_edited** | **bool** | Whether future transaction was edited | [optional] 
**import_id** | **int** | Import batch ID | [optional] 
**import_hash** | **str** | Import hash for deduplication | [optional] 
**forex** | **str** | Foreign exchange rate | [optional] 

## Example

```python
from orbuculum_client.models.transaction import Transaction

# TODO update the JSON string below
json = "{}"
# create an instance of Transaction from a JSON string
transaction_instance = Transaction.from_json(json)
# print the JSON string representation of the object
print(Transaction.to_json())

# convert the object into a dict
transaction_dict = transaction_instance.to_dict()
# create an instance of Transaction from a dict
transaction_from_dict = Transaction.from_dict(transaction_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


