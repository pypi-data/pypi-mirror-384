# AddCommissionRequest

Request body for adding commission to a transaction

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workspace_id** | **int** | Workspace ID | 
**id** | **int** | Transaction ID | 
**commission** | [**CommissionData**](CommissionData.md) |  | 
**commission_side** | **str** | Commission side (sender/receiver) | [optional] 

## Example

```python
from orbuculum_client.models.add_commission_request import AddCommissionRequest

# TODO update the JSON string below
json = "{}"
# create an instance of AddCommissionRequest from a JSON string
add_commission_request_instance = AddCommissionRequest.from_json(json)
# print the JSON string representation of the object
print(AddCommissionRequest.to_json())

# convert the object into a dict
add_commission_request_dict = add_commission_request_instance.to_dict()
# create an instance of AddCommissionRequest from a dict
add_commission_request_from_dict = AddCommissionRequest.from_dict(add_commission_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


