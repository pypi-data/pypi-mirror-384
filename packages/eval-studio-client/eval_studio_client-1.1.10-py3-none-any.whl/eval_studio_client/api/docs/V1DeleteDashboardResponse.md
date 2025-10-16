# V1DeleteDashboardResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**dashboard** | [**V1Dashboard**](V1Dashboard.md) |  | [optional] 

## Example

```python
from eval_studio_client.api.models.v1_delete_dashboard_response import V1DeleteDashboardResponse

# TODO update the JSON string below
json = "{}"
# create an instance of V1DeleteDashboardResponse from a JSON string
v1_delete_dashboard_response_instance = V1DeleteDashboardResponse.from_json(json)
# print the JSON string representation of the object
print(V1DeleteDashboardResponse.to_json())

# convert the object into a dict
v1_delete_dashboard_response_dict = v1_delete_dashboard_response_instance.to_dict()
# create an instance of V1DeleteDashboardResponse from a dict
v1_delete_dashboard_response_from_dict = V1DeleteDashboardResponse.from_dict(v1_delete_dashboard_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


