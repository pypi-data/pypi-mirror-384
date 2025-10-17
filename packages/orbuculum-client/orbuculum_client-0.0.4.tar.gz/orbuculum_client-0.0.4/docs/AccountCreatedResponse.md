# AccountCreatedResponse

Response after successfully creating an account

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **int** | HTTP status code | 
**id** | **int** | Created account ID | 
**message** | **str** | Success message | 

## Example

```python
from orbuculum_client.models.account_created_response import AccountCreatedResponse

# TODO update the JSON string below
json = "{}"
# create an instance of AccountCreatedResponse from a JSON string
account_created_response_instance = AccountCreatedResponse.from_json(json)
# print the JSON string representation of the object
print(AccountCreatedResponse.to_json())

# convert the object into a dict
account_created_response_dict = account_created_response_instance.to_dict()
# create an instance of AccountCreatedResponse from a dict
account_created_response_from_dict = AccountCreatedResponse.from_dict(account_created_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


