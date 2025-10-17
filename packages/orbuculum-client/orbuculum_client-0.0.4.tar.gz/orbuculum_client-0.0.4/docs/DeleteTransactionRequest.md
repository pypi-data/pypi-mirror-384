# DeleteTransactionRequest

Request body for deleting a transaction

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_id** | **int** | Workspace ID | 
**id** | **int** | Transaction ID to delete | 

## Example

```python
from orbuculum_client.models.delete_transaction_request import DeleteTransactionRequest

# TODO update the JSON string below
json = "{}"
# create an instance of DeleteTransactionRequest from a JSON string
delete_transaction_request_instance = DeleteTransactionRequest.from_json(json)
# print the JSON string representation of the object
print(DeleteTransactionRequest.to_json())

# convert the object into a dict
delete_transaction_request_dict = delete_transaction_request_instance.to_dict()
# create an instance of DeleteTransactionRequest from a dict
delete_transaction_request_from_dict = DeleteTransactionRequest.from_dict(delete_transaction_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


