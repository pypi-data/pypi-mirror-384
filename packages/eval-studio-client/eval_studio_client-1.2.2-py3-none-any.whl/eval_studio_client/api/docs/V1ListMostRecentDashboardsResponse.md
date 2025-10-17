# V1ListMostRecentDashboardsResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**dashboards** | [**List[V1Dashboard]**](V1Dashboard.md) | The list of Dashboards. | [optional] 

## Example

```python
from eval_studio_client.api.models.v1_list_most_recent_dashboards_response import V1ListMostRecentDashboardsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of V1ListMostRecentDashboardsResponse from a JSON string
v1_list_most_recent_dashboards_response_instance = V1ListMostRecentDashboardsResponse.from_json(json)
# print the JSON string representation of the object
print(V1ListMostRecentDashboardsResponse.to_json())

# convert the object into a dict
v1_list_most_recent_dashboards_response_dict = v1_list_most_recent_dashboards_response_instance.to_dict()
# create an instance of V1ListMostRecentDashboardsResponse from a dict
v1_list_most_recent_dashboards_response_from_dict = V1ListMostRecentDashboardsResponse.from_dict(v1_list_most_recent_dashboards_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


