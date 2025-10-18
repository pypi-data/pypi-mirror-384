# ProjectUpdate


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**colour** | **str** |  | [optional] 
**locations** | [**List[Location]**](Location.md) |  | [optional] 
**name** | **str** |  | [optional] 
**note** | **str** |  | [optional] 

## Example

```python
from spice_client.models.project_update import ProjectUpdate

# TODO update the JSON string below
json = "{}"
# create an instance of ProjectUpdate from a JSON string
project_update_instance = ProjectUpdate.from_json(json)
# print the JSON string representation of the object
print(ProjectUpdate.to_json())

# convert the object into a dict
project_update_dict = project_update_instance.to_dict()
# create an instance of ProjectUpdate from a dict
project_update_from_dict = ProjectUpdate.from_dict(project_update_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


