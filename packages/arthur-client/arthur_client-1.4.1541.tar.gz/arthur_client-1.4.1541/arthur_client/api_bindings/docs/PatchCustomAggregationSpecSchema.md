# PatchCustomAggregationSpecSchema


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | [optional] 
**description** | **str** |  | [optional] 

## Example

```python
from arthur_client.api_bindings.models.patch_custom_aggregation_spec_schema import PatchCustomAggregationSpecSchema

# TODO update the JSON string below
json = "{}"
# create an instance of PatchCustomAggregationSpecSchema from a JSON string
patch_custom_aggregation_spec_schema_instance = PatchCustomAggregationSpecSchema.from_json(json)
# print the JSON string representation of the object
print(PatchCustomAggregationSpecSchema.to_json())

# convert the object into a dict
patch_custom_aggregation_spec_schema_dict = patch_custom_aggregation_spec_schema_instance.to_dict()
# create an instance of PatchCustomAggregationSpecSchema from a dict
patch_custom_aggregation_spec_schema_from_dict = PatchCustomAggregationSpecSchema.from_dict(patch_custom_aggregation_spec_schema_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


