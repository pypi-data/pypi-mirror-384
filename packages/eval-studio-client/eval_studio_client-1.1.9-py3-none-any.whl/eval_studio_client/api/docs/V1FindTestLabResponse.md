# V1FindTestLabResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**test_lab** | [**V1TestLab**](V1TestLab.md) |  | [optional] 

## Example

```python
from eval_studio_client.api.models.v1_find_test_lab_response import V1FindTestLabResponse

# TODO update the JSON string below
json = "{}"
# create an instance of V1FindTestLabResponse from a JSON string
v1_find_test_lab_response_instance = V1FindTestLabResponse.from_json(json)
# print the JSON string representation of the object
print(V1FindTestLabResponse.to_json())

# convert the object into a dict
v1_find_test_lab_response_dict = v1_find_test_lab_response_instance.to_dict()
# create an instance of V1FindTestLabResponse from a dict
v1_find_test_lab_response_from_dict = V1FindTestLabResponse.from_dict(v1_find_test_lab_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


