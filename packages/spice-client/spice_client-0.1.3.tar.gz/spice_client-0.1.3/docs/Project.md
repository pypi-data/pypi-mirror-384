# Project


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**colour** | **str** |  | [optional] 
**created_at** | **datetime** |  | 
**id** | **str** |  | 
**last_updated** | **datetime** |  | 
**locations** | [**List[Location]**](Location.md) |  | 
**name** | **str** |  | 
**note** | **str** |  | [optional] 

## Example

```python
from spice_client.models.project import Project

# TODO update the JSON string below
json = "{}"
# create an instance of Project from a JSON string
project_instance = Project.from_json(json)
# print the JSON string representation of the object
print(Project.to_json())

# convert the object into a dict
project_dict = project_instance.to_dict()
# create an instance of Project from a dict
project_from_dict = Project.from_dict(project_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


