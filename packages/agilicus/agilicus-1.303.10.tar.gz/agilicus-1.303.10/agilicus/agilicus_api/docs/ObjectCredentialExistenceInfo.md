# ObjectCredentialExistenceInfo

A simple object describing whether or not object credentials exist. Holds only the most basic information since it exposed through a less restricted endpoint. 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**credential_id** | **str** | Unique identifier | [optional] 
**object_id** | **str** | Unique identifier | [optional] 
**object_type** | [**ObjectType**](ObjectType.md) |  | [optional] 
**org_id** | **str** | Unique identifier | [optional] 
**purpose** | [**CredentialPurpose**](CredentialPurpose.md) |  | [optional] 
**resource_members** | [**[ResourceMember]**](ResourceMember.md) | A list of resources that are associated with this Credential. This would be populated if the credential type is a group. | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


