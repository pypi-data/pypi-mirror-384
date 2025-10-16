# CommissionData

Commission calculation data

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**sender_amount** | **str** | Commission sender amount | 
**receiver_amount** | **str** | Commission receiver amount | 

## Example

```python
from orbuculum_client.models.commission_data import CommissionData

# TODO update the JSON string below
json = "{}"
# create an instance of CommissionData from a JSON string
commission_data_instance = CommissionData.from_json(json)
# print the JSON string representation of the object
print(CommissionData.to_json())

# convert the object into a dict
commission_data_dict = commission_data_instance.to_dict()
# create an instance of CommissionData from a dict
commission_data_from_dict = CommissionData.from_dict(commission_data_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


