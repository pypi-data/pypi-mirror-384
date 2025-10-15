# LoggedInInjection

Configuration specific to injected client javascript, to determine if the client is logged in. 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** | How logged in is determined, such as:   - automatic        automtically determine how the client is logged in   - fetch        logged in is determined with a fetch path  | 
**fetch_path** | **str** | The fetch path to determine if the client is logged in. A successful login to this api path will result in a 200 OK.  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


