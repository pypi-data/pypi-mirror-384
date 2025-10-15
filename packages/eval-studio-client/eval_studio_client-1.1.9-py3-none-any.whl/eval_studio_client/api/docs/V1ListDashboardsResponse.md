# V1ListDashboardsResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**dashboards** | [**List[V1Dashboard]**](V1Dashboard.md) | The list of Dashboards. | [optional] 

## Example

```python
from eval_studio_client.api.models.v1_list_dashboards_response import V1ListDashboardsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of V1ListDashboardsResponse from a JSON string
v1_list_dashboards_response_instance = V1ListDashboardsResponse.from_json(json)
# print the JSON string representation of the object
print(V1ListDashboardsResponse.to_json())

# convert the object into a dict
v1_list_dashboards_response_dict = v1_list_dashboards_response_instance.to_dict()
# create an instance of V1ListDashboardsResponse from a dict
v1_list_dashboards_response_from_dict = V1ListDashboardsResponse.from_dict(v1_list_dashboards_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


