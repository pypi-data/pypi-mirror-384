# V1DeleteWorkflowResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**workflow** | [**V1Workflow**](V1Workflow.md) |  | [optional] 

## Example

```python
from eval_studio_client.api.models.v1_delete_workflow_response import V1DeleteWorkflowResponse

# TODO update the JSON string below
json = "{}"
# create an instance of V1DeleteWorkflowResponse from a JSON string
v1_delete_workflow_response_instance = V1DeleteWorkflowResponse.from_json(json)
# print the JSON string representation of the object
print(V1DeleteWorkflowResponse.to_json())

# convert the object into a dict
v1_delete_workflow_response_dict = v1_delete_workflow_response_instance.to_dict()
# create an instance of V1DeleteWorkflowResponse from a dict
v1_delete_workflow_response_from_dict = V1DeleteWorkflowResponse.from_dict(v1_delete_workflow_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


