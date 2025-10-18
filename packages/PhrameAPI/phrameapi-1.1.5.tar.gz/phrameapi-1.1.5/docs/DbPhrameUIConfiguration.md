# DbPhrameUIConfiguration

target resolution of a display

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | [optional] 
**left** | **int** |  | [optional] 
**top** | **int** |  | [optional] 
**width** | **int** |  | [optional] 
**height** | **int** |  | [optional] 
**type** | **str** |  | [optional] 
**z_order** | **int** |  | [optional] 
**stream_id** | **str** |  | [optional] 
**stream_suffix** | **str** |  | [optional] 
**button_label** | **str** |  | [optional] 
**group_id** | **str** |  | [optional] 

## Example

```python
from PhrameAPI.models.db_phrame_ui_configuration import DbPhrameUIConfiguration

# TODO update the JSON string below
json = "{}"
# create an instance of DbPhrameUIConfiguration from a JSON string
db_phrame_ui_configuration_instance = DbPhrameUIConfiguration.from_json(json)
# print the JSON string representation of the object
print(DbPhrameUIConfiguration.to_json())

# convert the object into a dict
db_phrame_ui_configuration_dict = db_phrame_ui_configuration_instance.to_dict()
# create an instance of DbPhrameUIConfiguration from a dict
db_phrame_ui_configuration_from_dict = DbPhrameUIConfiguration.from_dict(db_phrame_ui_configuration_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


