# UpdateLabelResponseData

Updated label data

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** | Label ID | [optional] 
**name** | **str** | Label name | [optional] 
**color** | **int** | Label color code | [optional] 
**icon** | **int** | Label icon code | [optional] 

## Example

```python
from orbuculum_client.models.update_label_response_data import UpdateLabelResponseData

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateLabelResponseData from a JSON string
update_label_response_data_instance = UpdateLabelResponseData.from_json(json)
# print the JSON string representation of the object
print(UpdateLabelResponseData.to_json())

# convert the object into a dict
update_label_response_data_dict = update_label_response_data_instance.to_dict()
# create an instance of UpdateLabelResponseData from a dict
update_label_response_data_from_dict = UpdateLabelResponseData.from_dict(update_label_response_data_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


