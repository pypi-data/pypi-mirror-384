# LabelCreatedResponseData

Created label data

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** | Created label ID | [optional] 
**name** | **str** | Label name | [optional] 
**color** | **int** | Label color code | [optional] 
**icon** | **int** | Label icon code | [optional] 

## Example

```python
from orbuculum_client.models.label_created_response_data import LabelCreatedResponseData

# TODO update the JSON string below
json = "{}"
# create an instance of LabelCreatedResponseData from a JSON string
label_created_response_data_instance = LabelCreatedResponseData.from_json(json)
# print the JSON string representation of the object
print(LabelCreatedResponseData.to_json())

# convert the object into a dict
label_created_response_data_dict = label_created_response_data_instance.to_dict()
# create an instance of LabelCreatedResponseData from a dict
label_created_response_data_from_dict = LabelCreatedResponseData.from_dict(label_created_response_data_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


