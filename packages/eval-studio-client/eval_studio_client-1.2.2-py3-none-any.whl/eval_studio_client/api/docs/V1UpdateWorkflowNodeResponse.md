# V1UpdateWorkflowNodeResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**node** | [**V1WorkflowNode**](V1WorkflowNode.md) |  | [optional] 

## Example

```python
from eval_studio_client.api.models.v1_update_workflow_node_response import V1UpdateWorkflowNodeResponse

# TODO update the JSON string below
json = "{}"
# create an instance of V1UpdateWorkflowNodeResponse from a JSON string
v1_update_workflow_node_response_instance = V1UpdateWorkflowNodeResponse.from_json(json)
# print the JSON string representation of the object
print(V1UpdateWorkflowNodeResponse.to_json())

# convert the object into a dict
v1_update_workflow_node_response_dict = v1_update_workflow_node_response_instance.to_dict()
# create an instance of V1UpdateWorkflowNodeResponse from a dict
v1_update_workflow_node_response_from_dict = V1UpdateWorkflowNodeResponse.from_dict(v1_update_workflow_node_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


