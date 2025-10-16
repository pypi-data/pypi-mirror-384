# CustomTableInfo

Information about a custom table including its structure

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**api_table_name** | **str** | Table name for API requests (without &#39;c_&#39; prefix) | [optional] 
**db_table_name** | **str** | Actual table name in database with &#39;c_&#39; prefix | [optional] 
**columns** | [**List[ColumnInfo]**](ColumnInfo.md) | Array of column information | [optional] 

## Example

```python
from orbuculum_client.models.custom_table_info import CustomTableInfo

# TODO update the JSON string below
json = "{}"
# create an instance of CustomTableInfo from a JSON string
custom_table_info_instance = CustomTableInfo.from_json(json)
# print the JSON string representation of the object
print(CustomTableInfo.to_json())

# convert the object into a dict
custom_table_info_dict = custom_table_info_instance.to_dict()
# create an instance of CustomTableInfo from a dict
custom_table_info_from_dict = CustomTableInfo.from_dict(custom_table_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


