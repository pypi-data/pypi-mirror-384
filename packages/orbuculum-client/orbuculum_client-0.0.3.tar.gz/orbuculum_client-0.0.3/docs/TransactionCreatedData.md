# TransactionCreatedData


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** | Created transaction ID | 
**apikey** | **str** | API key | [optional] 
**sender_commission_id** | **int** | Sender commission transaction ID | [optional] 
**receiver_commission_id** | **int** | Receiver commission transaction ID | [optional] 

## Example

```python
from orbuculum_client.models.transaction_created_data import TransactionCreatedData

# TODO update the JSON string below
json = "{}"
# create an instance of TransactionCreatedData from a JSON string
transaction_created_data_instance = TransactionCreatedData.from_json(json)
# print the JSON string representation of the object
print(TransactionCreatedData.to_json())

# convert the object into a dict
transaction_created_data_dict = transaction_created_data_instance.to_dict()
# create an instance of TransactionCreatedData from a dict
transaction_created_data_from_dict = TransactionCreatedData.from_dict(transaction_created_data_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


