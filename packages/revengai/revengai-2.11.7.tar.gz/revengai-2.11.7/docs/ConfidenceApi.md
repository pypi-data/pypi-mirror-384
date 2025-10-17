# revengai.ConfidenceApi

All URIs are relative to *https://api.reveng.ai*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_analysis_tag_score**](ConfidenceApi.md#get_analysis_tag_score) | **POST** /v2/confidence/analysis/{analysis_id}/tag_score | Calculate Tag Confidence Score for an Analysis


# **get_analysis_tag_score**
> BaseResponseListTagOriginBoxPlotConfidence get_analysis_tag_score(analysis_id, tag_confidence_body)

Calculate Tag Confidence Score for an Analysis

Accepts a analysis ID and a list of tags, returns the confidence score for each tag in the list

### Example

* Api Key Authentication (APIKey):

```python
import revengai
from revengai.models.base_response_list_tag_origin_box_plot_confidence import BaseResponseListTagOriginBoxPlotConfidence
from revengai.models.tag_confidence_body import TagConfidenceBody
from revengai.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.reveng.ai
# See configuration.py for a list of all supported configuration parameters.
configuration = revengai.Configuration(
    host = "https://api.reveng.ai"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: APIKey
configuration.api_key['APIKey'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['APIKey'] = 'Bearer'

# Enter a context with an instance of the API client
with revengai.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = revengai.ConfidenceApi(api_client)
    analysis_id = 56 # int | The analysis to calculate the tag scores for
    tag_confidence_body = revengai.TagConfidenceBody() # TagConfidenceBody | 

    try:
        # Calculate Tag Confidence Score for an Analysis
        api_response = api_instance.get_analysis_tag_score(analysis_id, tag_confidence_body)
        print("The response of ConfidenceApi->get_analysis_tag_score:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ConfidenceApi->get_analysis_tag_score: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **analysis_id** | **int**| The analysis to calculate the tag scores for | 
 **tag_confidence_body** | [**TagConfidenceBody**](TagConfidenceBody.md)|  | 

### Return type

[**BaseResponseListTagOriginBoxPlotConfidence**](BaseResponseListTagOriginBoxPlotConfidence.md)

### Authorization

[APIKey](../README.md#APIKey)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Invalid request parameters |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

