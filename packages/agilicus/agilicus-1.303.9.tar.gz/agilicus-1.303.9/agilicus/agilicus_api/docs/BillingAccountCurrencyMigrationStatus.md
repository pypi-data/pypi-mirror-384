# BillingAccountCurrencyMigrationStatus

The result of the migration. 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**result** | **str** | The result of the migration.  - &#x60;migrated&#x60;: the migration succeeded - &#x60;nop&#x60;: no change was necessary  | 
**new_customer_id** | **str** | The ID of the new customer created in the migration  | [optional] 
**new_subscriptions** | **[str]** | The new subscriptions created in the migration. Note that these may actually be subscription schedules.  | [optional] 
**new_billing_account_id** | **str** | Unique identifier | [optional] 
**new_billing_subscription_ids** | **[str]** | The GUIDs of the newly created billing subscriptions | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


