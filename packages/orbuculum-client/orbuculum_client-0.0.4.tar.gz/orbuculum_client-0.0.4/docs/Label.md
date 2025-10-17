# Label

Label object with all details

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** | Label ID | [optional] 
**name** | **str** | Label name | [optional] 
**color** | **int** | Label color code | [optional] 
**icon** | **int** | Label icon code | [optional] 
**is_default** | **bool** | Whether this is a default label | [optional] 

## Example

```python
from orbuculum_client.models.label import Label

# TODO update the JSON string below
json = "{}"
# create an instance of Label from a JSON string
label_instance = Label.from_json(json)
# print the JSON string representation of the object
print(Label.to_json())

# convert the object into a dict
label_dict = label_instance.to_dict()
# create an instance of Label from a dict
label_from_dict = Label.from_dict(label_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


