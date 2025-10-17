# orbuculum_client.LimitationApi

All URIs are relative to *https://s1.orbuculum.app*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_limitation**](LimitationApi.md#get_limitation) | **GET** /api/limitation/get | Get transaction limitations for an account
[**manage_account_limitation**](LimitationApi.md#manage_account_limitation) | **POST** /api/limitation/account-manage | Manage account transaction limitations
[**manage_entity_limitation**](LimitationApi.md#manage_entity_limitation) | **POST** /api/limitation/entity-manage | Manage entity transaction limitations


# **get_limitation**
> GetLimitationsResponse get_limitation(workspace_id, account_id, project_id=project_id)

Get transaction limitations for an account

Retrieves account transaction restrictions (account-to-account and account-to-entity limitations)

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import orbuculum_client
from orbuculum_client.models.get_limitations_response import GetLimitationsResponse
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
    api_instance = orbuculum_client.LimitationApi(api_client)
    workspace_id = 1 # int | Workspace ID
    account_id = 1 # int | Account ID to get limitations for
    project_id = 1 # int | Project label ID (optional filter) (optional)

    try:
        # Get transaction limitations for an account
        api_response = api_instance.get_limitation(workspace_id, account_id, project_id=project_id)
        print("The response of LimitationApi->get_limitation:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LimitationApi->get_limitation: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **workspace_id** | **int**| Workspace ID | 
 **account_id** | **int**| Account ID to get limitations for | 
 **project_id** | **int**| Project label ID (optional filter) | [optional] 

### Return type

[**GetLimitationsResponse**](GetLimitationsResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Account limitations retrieved successfully |  -  |
**400** | Bad request - validation failed |  -  |
**401** | Unauthorized |  -  |
**403** | Forbidden - insufficient permissions |  -  |
**404** | Resource not found |  -  |
**405** | Method not allowed |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **manage_account_limitation**
> LimitationManagedResponse manage_account_limitation(manage_account_limitation_request)

Manage account transaction limitations

Creates, updates, or removes transaction restrictions between accounts (send/receive permissions)

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import orbuculum_client
from orbuculum_client.models.limitation_managed_response import LimitationManagedResponse
from orbuculum_client.models.manage_account_limitation_request import ManageAccountLimitationRequest
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
    api_instance = orbuculum_client.LimitationApi(api_client)
    manage_account_limitation_request = orbuculum_client.ManageAccountLimitationRequest() # ManageAccountLimitationRequest | 

    try:
        # Manage account transaction limitations
        api_response = api_instance.manage_account_limitation(manage_account_limitation_request)
        print("The response of LimitationApi->manage_account_limitation:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LimitationApi->manage_account_limitation: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **manage_account_limitation_request** | [**ManageAccountLimitationRequest**](ManageAccountLimitationRequest.md)|  | 

### Return type

[**LimitationManagedResponse**](LimitationManagedResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Account limitation managed successfully |  -  |
**400** | Bad request - validation failed |  -  |
**401** | Unauthorized |  -  |
**404** | Resource not found |  -  |
**405** | Method not allowed |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **manage_entity_limitation**
> LimitationManagedResponse manage_entity_limitation(manage_entity_limitation_request)

Manage entity transaction limitations

Creates, updates, or removes transaction restrictions between account and entity (send/receive permissions)

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import orbuculum_client
from orbuculum_client.models.limitation_managed_response import LimitationManagedResponse
from orbuculum_client.models.manage_entity_limitation_request import ManageEntityLimitationRequest
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
    api_instance = orbuculum_client.LimitationApi(api_client)
    manage_entity_limitation_request = orbuculum_client.ManageEntityLimitationRequest() # ManageEntityLimitationRequest | 

    try:
        # Manage entity transaction limitations
        api_response = api_instance.manage_entity_limitation(manage_entity_limitation_request)
        print("The response of LimitationApi->manage_entity_limitation:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LimitationApi->manage_entity_limitation: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **manage_entity_limitation_request** | [**ManageEntityLimitationRequest**](ManageEntityLimitationRequest.md)|  | 

### Return type

[**LimitationManagedResponse**](LimitationManagedResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Entity limitation managed successfully |  -  |
**400** | Bad request - validation failed |  -  |
**401** | Unauthorized |  -  |
**404** | Resource not found |  -  |
**405** | Method not allowed |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

