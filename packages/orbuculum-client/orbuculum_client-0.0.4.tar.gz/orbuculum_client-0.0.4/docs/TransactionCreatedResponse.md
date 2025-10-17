# TransactionCreatedResponse

Response after successfully creating a transaction

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | 
**data** | [**TransactionCreatedData**](TransactionCreatedData.md) |  | 

## Example

```python
from orbuculum_client.models.transaction_created_response import TransactionCreatedResponse

# TODO update the JSON string below
json = "{}"
# create an instance of TransactionCreatedResponse from a JSON string
transaction_created_response_instance = TransactionCreatedResponse.from_json(json)
# print the JSON string representation of the object
print(TransactionCreatedResponse.to_json())

# convert the object into a dict
transaction_created_response_dict = transaction_created_response_instance.to_dict()
# create an instance of TransactionCreatedResponse from a dict
transaction_created_response_from_dict = TransactionCreatedResponse.from_dict(transaction_created_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


