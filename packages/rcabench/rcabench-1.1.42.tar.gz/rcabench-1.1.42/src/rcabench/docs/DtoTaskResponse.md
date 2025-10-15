# DtoTaskResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**created_at** | **str** |  | [optional] 
**group_id** | **str** |  | [optional] 
**id** | **str** |  | [optional] 
**immediate** | **bool** |  | [optional] 
**logs** | **List[str]** | Only included when specifically requested | [optional] 
**project** | [**DtoProjectResponse**](DtoProjectResponse.md) |  | [optional] 
**project_id** | **int** |  | [optional] 
**status** | **str** |  | [optional] 
**trace_id** | **str** |  | [optional] 
**type** | **str** |  | [optional] 
**updated_at** | **str** |  | [optional] 

## Example

```python
from rcabench.openapi.models.dto_task_response import DtoTaskResponse

# TODO update the JSON string below
json = "{}"
# create an instance of DtoTaskResponse from a JSON string
dto_task_response_instance = DtoTaskResponse.from_json(json)
# print the JSON string representation of the object
print DtoTaskResponse.to_json()

# convert the object into a dict
dto_task_response_dict = dto_task_response_instance.to_dict()
# create an instance of DtoTaskResponse from a dict
dto_task_response_form_dict = dto_task_response.from_dict(dto_task_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


