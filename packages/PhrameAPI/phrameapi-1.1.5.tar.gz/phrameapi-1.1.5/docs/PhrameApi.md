# PhrameAPI.PhrameApi

All URIs are relative to *http://localhost/PhrameServer*

Method | HTTP request | Description
------------- | ------------- | -------------
[**minio_delete_ui_component**](PhrameApi.md#minio_delete_ui_component) | **DELETE** /components | DELETE Component
[**minio_delete_ui_config**](PhrameApi.md#minio_delete_ui_config) | **DELETE** /config | DELETE config
[**minio_get_all_component_names**](PhrameApi.md#minio_get_all_component_names) | **GET** /components/all | Get all components
[**minio_get_all_config_names**](PhrameApi.md#minio_get_all_config_names) | **GET** /config/all | GET all configs
[**minio_get_ui_component**](PhrameApi.md#minio_get_ui_component) | **GET** /components | GET Components
[**minio_get_ui_config**](PhrameApi.md#minio_get_ui_config) | **GET** /config | GET config
[**minio_post_ui_component**](PhrameApi.md#minio_post_ui_component) | **POST** /components | POST component
[**minio_post_ui_config**](PhrameApi.md#minio_post_ui_config) | **POST** /config | POST config


# **minio_delete_ui_component**
> minio_delete_ui_component(component_name, version_id=version_id)

DELETE Component

### Example


```python
import PhrameAPI
from PhrameAPI.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost/PhrameServer
# See configuration.py for a list of all supported configuration parameters.
configuration = PhrameAPI.Configuration(
    host = "http://localhost/PhrameServer"
)


# Enter a context with an instance of the API client
with PhrameAPI.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = PhrameAPI.PhrameApi(api_client)
    component_name = 'component_name_example' # str | Name of component
    version_id = 'version_id_example' # str | ID of component (optional)

    try:
        # DELETE Component
        api_instance.minio_delete_ui_component(component_name, version_id=version_id)
    except Exception as e:
        print("Exception when calling PhrameApi->minio_delete_ui_component: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **component_name** | **str**| Name of component | 
 **version_id** | **str**| ID of component | [optional] 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**201** | Created |  -  |
**400** | Bad Request |  -  |
**401** | Unauthorized |  -  |
**403** | Forbidden |  -  |
**404** | Not Found |  -  |
**500** | Internal Server Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **minio_delete_ui_config**
> minio_delete_ui_config(config_name, version_id=version_id)

DELETE config

 DELETE the UI config for a provided config name

### Example


```python
import PhrameAPI
from PhrameAPI.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost/PhrameServer
# See configuration.py for a list of all supported configuration parameters.
configuration = PhrameAPI.Configuration(
    host = "http://localhost/PhrameServer"
)


# Enter a context with an instance of the API client
with PhrameAPI.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = PhrameAPI.PhrameApi(api_client)
    config_name = 'config_name_example' # str | Name of Configuration
    version_id = 'version_id_example' # str | Version ID of obj (optional)

    try:
        # DELETE config
        api_instance.minio_delete_ui_config(config_name, version_id=version_id)
    except Exception as e:
        print("Exception when calling PhrameApi->minio_delete_ui_config: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **config_name** | **str**| Name of Configuration | 
 **version_id** | **str**| Version ID of obj | [optional] 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**201** | Created |  -  |
**202** | Accepted |  -  |
**203** | Non-Authoritative Information |  -  |
**400** | Bad Request |  -  |
**401** | Unauthorized |  -  |
**403** | Forbidden |  -  |
**404** | Not Found |  -  |
**500** | Internal Server Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **minio_get_all_component_names**
> object minio_get_all_component_names()

Get all components

 GET all the available UI components

### Example


```python
import PhrameAPI
from PhrameAPI.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost/PhrameServer
# See configuration.py for a list of all supported configuration parameters.
configuration = PhrameAPI.Configuration(
    host = "http://localhost/PhrameServer"
)


# Enter a context with an instance of the API client
with PhrameAPI.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = PhrameAPI.PhrameApi(api_client)

    try:
        # Get all components
        api_response = api_instance.minio_get_all_component_names()
        print("The response of PhrameApi->minio_get_all_component_names:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling PhrameApi->minio_get_all_component_names: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**201** | Created |  -  |
**400** | Bad Request |  -  |
**401** | Unauthorized |  -  |
**403** | Forbidden |  -  |
**404** | Not Found |  -  |
**500** | Internal Server Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **minio_get_all_config_names**
> object minio_get_all_config_names(suffix=suffix)

GET all configs

 GET all the available UI configs  

### Example


```python
import PhrameAPI
from PhrameAPI.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost/PhrameServer
# See configuration.py for a list of all supported configuration parameters.
configuration = PhrameAPI.Configuration(
    host = "http://localhost/PhrameServer"
)


# Enter a context with an instance of the API client
with PhrameAPI.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = PhrameAPI.PhrameApi(api_client)
    suffix = 'suffix_example' # str | Suffix or file extension to filter (optional)

    try:
        # GET all configs
        api_response = api_instance.minio_get_all_config_names(suffix=suffix)
        print("The response of PhrameApi->minio_get_all_config_names:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling PhrameApi->minio_get_all_config_names: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **suffix** | **str**| Suffix or file extension to filter | [optional] 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**400** | Bad Request |  -  |
**401** | Unauthorized |  -  |
**403** | Forbidden |  -  |
**404** | Not Found |  -  |
**500** | Internal Server Error |  -  |
**501** | Not Implemented |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **minio_get_ui_component**
> object minio_get_ui_component(component_name, version_id=version_id)

GET Components

 GET the UI component for a provided name 

### Example


```python
import PhrameAPI
from PhrameAPI.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost/PhrameServer
# See configuration.py for a list of all supported configuration parameters.
configuration = PhrameAPI.Configuration(
    host = "http://localhost/PhrameServer"
)


# Enter a context with an instance of the API client
with PhrameAPI.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = PhrameAPI.PhrameApi(api_client)
    component_name = 'component_name_example' # str | Name of component
    version_id = 'version_id_example' # str | ID of component (optional)

    try:
        # GET Components
        api_response = api_instance.minio_get_ui_component(component_name, version_id=version_id)
        print("The response of PhrameApi->minio_get_ui_component:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling PhrameApi->minio_get_ui_component: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **component_name** | **str**| Name of component | 
 **version_id** | **str**| ID of component | [optional] 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**201** | Created |  -  |
**202** | Accepted |  -  |
**400** | Bad Request |  -  |
**401** | Unauthorized |  -  |
**403** | Forbidden |  -  |
**404** | Not Found |  -  |
**500** | Internal Server Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **minio_get_ui_config**
> object minio_get_ui_config(config_name, version_id=version_id)

GET config

 GET the UI config for a provided config name 

### Example


```python
import PhrameAPI
from PhrameAPI.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost/PhrameServer
# See configuration.py for a list of all supported configuration parameters.
configuration = PhrameAPI.Configuration(
    host = "http://localhost/PhrameServer"
)


# Enter a context with an instance of the API client
with PhrameAPI.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = PhrameAPI.PhrameApi(api_client)
    config_name = 'DoubleSideView' # str | Name of Configuration
    version_id = 'version_id_example' # str | Version ID of obj (optional) (optional)

    try:
        # GET config
        api_response = api_instance.minio_get_ui_config(config_name, version_id=version_id)
        print("The response of PhrameApi->minio_get_ui_config:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling PhrameApi->minio_get_ui_config: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **config_name** | **str**| Name of Configuration | 
 **version_id** | **str**| Version ID of obj (optional) | [optional] 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**202** | Accepted |  -  |
**203** | Non-Authoritative Information |  -  |
**400** | Bad Request |  -  |
**401** | Unauthorized |  -  |
**403** | Forbidden |  -  |
**404** | Not Found |  -  |
**500** | Internal Server Error |  -  |
**501** | Not Implemented |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **minio_post_ui_component**
> minio_post_ui_component(component_name, body=body)

POST component

 POST the UI component for a provided config name

### Example


```python
import PhrameAPI
from PhrameAPI.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost/PhrameServer
# See configuration.py for a list of all supported configuration parameters.
configuration = PhrameAPI.Configuration(
    host = "http://localhost/PhrameServer"
)


# Enter a context with an instance of the API client
with PhrameAPI.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = PhrameAPI.PhrameApi(api_client)
    component_name = 'component_name_example' # str | Name of component
    body = None # object |  (optional)

    try:
        # POST component
        api_instance.minio_post_ui_component(component_name, body=body)
    except Exception as e:
        print("Exception when calling PhrameApi->minio_post_ui_component: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **component_name** | **str**| Name of component | 
 **body** | **object**|  | [optional] 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**201** | Created |  -  |
**400** | Bad Request |  -  |
**401** | Unauthorized |  -  |
**403** | Forbidden |  -  |
**404** | Not Found |  -  |
**500** | Internal Server Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **minio_post_ui_config**
> minio_post_ui_config(config_name, body=body)

POST config

 POST the UI config for a provided config name

### Example


```python
import PhrameAPI
from PhrameAPI.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost/PhrameServer
# See configuration.py for a list of all supported configuration parameters.
configuration = PhrameAPI.Configuration(
    host = "http://localhost/PhrameServer"
)


# Enter a context with an instance of the API client
with PhrameAPI.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = PhrameAPI.PhrameApi(api_client)
    config_name = 'config_name_example' # str | Name of config file
    body = {} # object |  (optional)

    try:
        # POST config
        api_instance.minio_post_ui_config(config_name, body=body)
    except Exception as e:
        print("Exception when calling PhrameApi->minio_post_ui_config: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **config_name** | **str**| Name of config file | 
 **body** | **object**|  | [optional] 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**201** | Created |  -  |
**400** | Bad Request |  -  |
**401** | Unauthorized |  -  |
**403** | Forbidden |  -  |
**404** | Not Found |  -  |
**500** | Internal Server Error |  -  |
**501** | Not Implemented |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

