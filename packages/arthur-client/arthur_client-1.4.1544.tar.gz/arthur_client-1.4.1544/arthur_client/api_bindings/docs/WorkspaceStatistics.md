# WorkspaceStatistics


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**active_engine_count** | **int** |  | 
**total_engine_count** | **int** |  | 
**projects_count** | **int** |  | 
**custom_agg_count** | **int** |  | 
**workspace_user_count** | **int** |  | 

## Example

```python
from arthur_client.api_bindings.models.workspace_statistics import WorkspaceStatistics

# TODO update the JSON string below
json = "{}"
# create an instance of WorkspaceStatistics from a JSON string
workspace_statistics_instance = WorkspaceStatistics.from_json(json)
# print the JSON string representation of the object
print(WorkspaceStatistics.to_json())

# convert the object into a dict
workspace_statistics_dict = workspace_statistics_instance.to_dict()
# create an instance of WorkspaceStatistics from a dict
workspace_statistics_from_dict = WorkspaceStatistics.from_dict(workspace_statistics_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


