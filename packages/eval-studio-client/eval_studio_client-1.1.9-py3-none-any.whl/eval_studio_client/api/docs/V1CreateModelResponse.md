# V1CreateModelResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**model** | [**V1Model**](V1Model.md) |  | [optional] 

## Example

```python
from eval_studio_client.api.models.v1_create_model_response import V1CreateModelResponse

# TODO update the JSON string below
json = "{}"
# create an instance of V1CreateModelResponse from a JSON string
v1_create_model_response_instance = V1CreateModelResponse.from_json(json)
# print the JSON string representation of the object
print(V1CreateModelResponse.to_json())

# convert the object into a dict
v1_create_model_response_dict = v1_create_model_response_instance.to_dict()
# create an instance of V1CreateModelResponse from a dict
v1_create_model_response_from_dict = V1CreateModelResponse.from_dict(v1_create_model_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


