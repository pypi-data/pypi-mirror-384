# orbuculum_client.AccountPermissionsApi

All URIs are relative to *https://s1.orbuculum.app*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_account_permission**](AccountPermissionsApi.md#create_account_permission) | **POST** /api/permission/account-create | Create account permission
[**delete_account_permission**](AccountPermissionsApi.md#delete_account_permission) | **DELETE** /api/permission/account-delete | Delete account permission
[**edit_account_permission**](AccountPermissionsApi.md#edit_account_permission) | **POST** /api/permission/account-edit | Permission to edit account
[**get_account_permissions**](AccountPermissionsApi.md#get_account_permissions) | **GET** /api/permission/account | Get account permissions


# **create_account_permission**
> PermissionCreatedResponse create_account_permission(create_account_permission_request)

Create account permission

Creates new permission settings for an account, defining access levels for users or roles

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import orbuculum_client
from orbuculum_client.models.create_account_permission_request import CreateAccountPermissionRequest
from orbuculum_client.models.permission_created_response import PermissionCreatedResponse
from orbuculum_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://s1.orbuculum.app
# See configuration.py for a list of all supported configuration parameters.
configuration = orbuculum_client.Configuration(
    host = "https://s1.orbuculum.app"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = orbuculum_client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with orbuculum_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = orbuculum_client.AccountPermissionsApi(api_client)
    create_account_permission_request = orbuculum_client.CreateAccountPermissionRequest() # CreateAccountPermissionRequest | 

    try:
        # Create account permission
        api_response = api_instance.create_account_permission(create_account_permission_request)
        print("The response of AccountPermissionsApi->create_account_permission:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AccountPermissionsApi->create_account_permission: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_account_permission_request** | [**CreateAccountPermissionRequest**](CreateAccountPermissionRequest.md)|  | 

### Return type

[**PermissionCreatedResponse**](PermissionCreatedResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Account permission created successfully |  -  |
**400** | Bad request - validation failed |  -  |
**401** | Unauthorized |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_account_permission**
> SuccessResponse delete_account_permission(workspace_id, permission_id)

Delete account permission

Removes permission settings for an account, revoking access for specified users or roles

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import orbuculum_client
from orbuculum_client.models.success_response import SuccessResponse
from orbuculum_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://s1.orbuculum.app
# See configuration.py for a list of all supported configuration parameters.
configuration = orbuculum_client.Configuration(
    host = "https://s1.orbuculum.app"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = orbuculum_client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with orbuculum_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = orbuculum_client.AccountPermissionsApi(api_client)
    workspace_id = 1 # int | Workspace ID
    permission_id = 1 # int | Permission ID to delete

    try:
        # Delete account permission
        api_response = api_instance.delete_account_permission(workspace_id, permission_id)
        print("The response of AccountPermissionsApi->delete_account_permission:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AccountPermissionsApi->delete_account_permission: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **workspace_id** | **int**| Workspace ID | 
 **permission_id** | **int**| Permission ID to delete | 

### Return type

[**SuccessResponse**](SuccessResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Account permission deleted successfully |  -  |
**400** | Bad request - validation failed |  -  |
**401** | Unauthorized |  -  |
**404** | Resource not found |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **edit_account_permission**
> SuccessResponse edit_account_permission(edit_account_permission_request)

Permission to edit account

Updates existing account permission settings, modifying access levels for users or roles

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import orbuculum_client
from orbuculum_client.models.edit_account_permission_request import EditAccountPermissionRequest
from orbuculum_client.models.success_response import SuccessResponse
from orbuculum_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://s1.orbuculum.app
# See configuration.py for a list of all supported configuration parameters.
configuration = orbuculum_client.Configuration(
    host = "https://s1.orbuculum.app"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = orbuculum_client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with orbuculum_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = orbuculum_client.AccountPermissionsApi(api_client)
    edit_account_permission_request = orbuculum_client.EditAccountPermissionRequest() # EditAccountPermissionRequest | 

    try:
        # Permission to edit account
        api_response = api_instance.edit_account_permission(edit_account_permission_request)
        print("The response of AccountPermissionsApi->edit_account_permission:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AccountPermissionsApi->edit_account_permission: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **edit_account_permission_request** | [**EditAccountPermissionRequest**](EditAccountPermissionRequest.md)|  | 

### Return type

[**SuccessResponse**](SuccessResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Account permission updated successfully |  -  |
**400** | Bad request - validation failed |  -  |
**401** | Unauthorized |  -  |
**404** | Resource not found |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_account_permissions**
> GetAccountPermissionsResponse get_account_permissions(workspace_id, account_id=account_id)

Get account permissions

Retrieves permissions for accounts including access levels and management rights

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import orbuculum_client
from orbuculum_client.models.get_account_permissions_response import GetAccountPermissionsResponse
from orbuculum_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://s1.orbuculum.app
# See configuration.py for a list of all supported configuration parameters.
configuration = orbuculum_client.Configuration(
    host = "https://s1.orbuculum.app"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = orbuculum_client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with orbuculum_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = orbuculum_client.AccountPermissionsApi(api_client)
    workspace_id = 1 # int | Workspace ID
    account_id = 1 # int | Specific account ID to get permissions for (optional)

    try:
        # Get account permissions
        api_response = api_instance.get_account_permissions(workspace_id, account_id=account_id)
        print("The response of AccountPermissionsApi->get_account_permissions:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AccountPermissionsApi->get_account_permissions: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **workspace_id** | **int**| Workspace ID | 
 **account_id** | **int**| Specific account ID to get permissions for | [optional] 

### Return type

[**GetAccountPermissionsResponse**](GetAccountPermissionsResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Account permissions retrieved successfully |  -  |
**400** | Bad request - validation failed |  -  |
**401** | Unauthorized |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

