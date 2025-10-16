# TransactionListResponse

Response containing list of transactions

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | 
**data** | [**List[Transaction]**](Transaction.md) | Array of transactions | 

## Example

```python
from orbuculum_client.models.transaction_list_response import TransactionListResponse

# TODO update the JSON string below
json = "{}"
# create an instance of TransactionListResponse from a JSON string
transaction_list_response_instance = TransactionListResponse.from_json(json)
# print the JSON string representation of the object
print(TransactionListResponse.to_json())

# convert the object into a dict
transaction_list_response_dict = transaction_list_response_instance.to_dict()
# create an instance of TransactionListResponse from a dict
transaction_list_response_from_dict = TransactionListResponse.from_dict(transaction_list_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


