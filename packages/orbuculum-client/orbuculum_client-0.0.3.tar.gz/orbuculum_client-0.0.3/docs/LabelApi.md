# orbuculum_client.LabelApi

All URIs are relative to *https://s1.orbuculum.app*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_label**](LabelApi.md#create_label) | **POST** /api/label/create | Create label
[**delete_label**](LabelApi.md#delete_label) | **DELETE** /api/label/delete | Delete an existing label
[**get_label**](LabelApi.md#get_label) | **GET** /api/label/get | Get label
[**update_label**](LabelApi.md#update_label) | **POST** /api/label/update | Update label


# **create_label**
> LabelCreatedResponse create_label(create_label_request)

Create label

Creates a new label for organizing and categorizing transactions

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import orbuculum_client
from orbuculum_client.models.create_label_request import CreateLabelRequest
from orbuculum_client.models.label_created_response import LabelCreatedResponse
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
    api_instance = orbuculum_client.LabelApi(api_client)
    create_label_request = orbuculum_client.CreateLabelRequest() # CreateLabelRequest | 

    try:
        # Create label
        api_response = api_instance.create_label(create_label_request)
        print("The response of LabelApi->create_label:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LabelApi->create_label: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_label_request** | [**CreateLabelRequest**](CreateLabelRequest.md)|  | 

### Return type

[**LabelCreatedResponse**](LabelCreatedResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Label created successfully |  -  |
**400** | Bad request - validation failed |  -  |
**401** | Unauthorized |  -  |
**403** | Forbidden - insufficient permissions |  -  |
**409** | Conflict - label name already exists |  -  |
**422** | Unprocessable entity - validation error |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_label**
> SuccessResponse delete_label(workspace_id, id)

Delete an existing label

Permanently deletes a label from the system. This action cannot be undone.

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
    api_instance = orbuculum_client.LabelApi(api_client)
    workspace_id = 1 # int | Workspace ID
    id = 1 # int | Label ID to delete

    try:
        # Delete an existing label
        api_response = api_instance.delete_label(workspace_id, id)
        print("The response of LabelApi->delete_label:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LabelApi->delete_label: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **workspace_id** | **int**| Workspace ID | 
 **id** | **int**| Label ID to delete | 

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
**200** | Label deleted successfully |  -  |
**400** | Bad request - validation failed |  -  |
**401** | Unauthorized |  -  |
**403** | Forbidden - insufficient permissions |  -  |
**404** | Resource not found |  -  |
**405** | Method not allowed |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_label**
> GetLabelsResponse get_label(workspace_id, project_id=project_id)

Get label

Retrieves label details for a specific project with optional filtering by label ID

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import orbuculum_client
from orbuculum_client.models.get_labels_response import GetLabelsResponse
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
    api_instance = orbuculum_client.LabelApi(api_client)
    workspace_id = 1 # int | Workspace ID
    project_id = 1 # int | Project ID (optional, to get specific label) (optional)

    try:
        # Get label
        api_response = api_instance.get_label(workspace_id, project_id=project_id)
        print("The response of LabelApi->get_label:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LabelApi->get_label: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **workspace_id** | **int**| Workspace ID | 
 **project_id** | **int**| Project ID (optional, to get specific label) | [optional] 

### Return type

[**GetLabelsResponse**](GetLabelsResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Label details retrieved successfully |  -  |
**400** | Bad request - validation failed |  -  |
**401** | Unauthorized |  -  |
**403** | Forbidden - insufficient permissions |  -  |
**404** | Resource not found |  -  |
**405** | Method not allowed |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_label**
> SuccessResponse update_label(update_label_request)

Update label

Updates an existing label with new name, color, or description

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import orbuculum_client
from orbuculum_client.models.success_response import SuccessResponse
from orbuculum_client.models.update_label_request import UpdateLabelRequest
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
    api_instance = orbuculum_client.LabelApi(api_client)
    update_label_request = orbuculum_client.UpdateLabelRequest() # UpdateLabelRequest | 

    try:
        # Update label
        api_response = api_instance.update_label(update_label_request)
        print("The response of LabelApi->update_label:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LabelApi->update_label: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **update_label_request** | [**UpdateLabelRequest**](UpdateLabelRequest.md)|  | 

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
**200** | Label updated successfully |  -  |
**400** | Bad request - validation failed |  -  |
**401** | Unauthorized |  -  |
**403** | Forbidden - insufficient permissions |  -  |
**404** | Resource not found |  -  |
**409** | Conflict - label name already exists |  -  |
**405** | Method not allowed |  -  |
**500** | Internal server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

