# LoginInjection

Configuration specific to injected client javascript. 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** | The type of login injection handled. Supported values are:  - form       http form based authentication, can be application/www-form-urlencoded or multipart/form-data  - automatic       Injection script will attempt to determine the type of login authentication automatically  - bearer       Bearer type authentication (eg. token)  - basic       http basic auth type authentication  | 
**inject_key_name** | **str** | Depending on the type of login handled, for example in form based login,  this property can be used by the form to signal to the backend connector facilitor  handling the login that the form should be handled as a login and populated.  | [optional]  if omitted the server will use the default value of ".agilicus-inject-credentials-config"
**fetch_config** | [**FetchInjection**](FetchInjection.md) |  | [optional] 
**logged_in_config** | [**LoggedInInjection**](LoggedInInjection.md) |  | [optional] 
**form_config** | [**FormInjection**](FormInjection.md) |  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


