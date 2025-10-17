# ColumnInfo

Information about a column in a custom table

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Column name | [optional] 
**type** | **str** | Column data type | [optional] 
**size** | **int** | Column size (if applicable) | [optional] 
**nullable** | **bool** | Whether column allows NULL values | [optional] 
**default** | **object** | Default value (if any) | [optional] 
**is_primary_key** | **bool** | Whether column is primary key | [optional] 

## Example

```python
from orbuculum_client.models.column_info import ColumnInfo

# TODO update the JSON string below
json = "{}"
# create an instance of ColumnInfo from a JSON string
column_info_instance = ColumnInfo.from_json(json)
# print the JSON string representation of the object
print(ColumnInfo.to_json())

# convert the object into a dict
column_info_dict = column_info_instance.to_dict()
# create an instance of ColumnInfo from a dict
column_info_from_dict = ColumnInfo.from_dict(column_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


