# DtoUnifiedTask


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cron_expr** | **str** | Cron expression for recurring tasks | [optional] 
**execute_time** | **int** | Unix timestamp for delayed execution | [optional] 
**group_carrier** | **Dict[str, str]** |  | [optional] 
**group_id** | **str** | ID for grouping tasks | [optional] 
**immediate** | **bool** | Whether to execute immediately | [optional] 
**payload** | **object** | Task-specific data | [optional] 
**project_id** | **int** | ID for the project (optional) | [optional] 
**restart_num** | **int** | Number of restarts for the task | [optional] 
**retry_policy** | [**DtoRetryPolicy**](DtoRetryPolicy.md) |  | [optional] 
**status** | **str** | Status of the task | [optional] 
**task_id** | **str** | Unique identifier for the task | [optional] 
**trace_carrier** | **Dict[str, str]** |  | [optional] 
**trace_id** | **str** | ID for tracing related tasks | [optional] 
**type** | [**ConstsTaskType**](ConstsTaskType.md) |  | [optional] 

## Example

```python
from rcabench.openapi.models.dto_unified_task import DtoUnifiedTask

# TODO update the JSON string below
json = "{}"
# create an instance of DtoUnifiedTask from a JSON string
dto_unified_task_instance = DtoUnifiedTask.from_json(json)
# print the JSON string representation of the object
print DtoUnifiedTask.to_json()

# convert the object into a dict
dto_unified_task_dict = dto_unified_task_instance.to_dict()
# create an instance of DtoUnifiedTask from a dict
dto_unified_task_form_dict = dto_unified_task.from_dict(dto_unified_task_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


