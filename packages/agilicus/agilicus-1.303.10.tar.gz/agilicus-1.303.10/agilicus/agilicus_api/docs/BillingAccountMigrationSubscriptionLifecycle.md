# BillingAccountMigrationSubscriptionLifecycle

Controls the lifecycle of subscriptions in the old and new billing accounts. 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**strategy** | **str** | The overall strategy for how to deprecate the old subscriptions and start new ones. - &#x60;start_now&#x60;: Ends the old subscription immediately and starts a new one, to be billed when the next one would have been. - &#x60;start_next_cycle&#x60;: Ends the old subscription when it complets its current cycle, and schedules the new one to start at the beginning of the next cycle.  | 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


