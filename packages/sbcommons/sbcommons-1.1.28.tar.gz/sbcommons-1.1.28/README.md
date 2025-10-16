# sbcommons
Packages shared between different lambda functions

---

### 1.1.28
* added Adp client from survey repo
### 1.1.26
* Added missing slash to save_df_to_s3
### 1.1.25
* More verbose logging when bulk updating profiles to make hunting down errors easier.
### ~~1.1.24~~ - Deprecated - bug with list length
* More verbose logging when bulk updating profiles to make hunting down errors easier.
### 1.1.23
* Enforcing stricter email validation.
### 1.1.22
* Changed a few things in the Klaviyo create bulk events payload to support date of event and other minor changes.
### 1.1.21
* Fixed bugs in Klaviyo client when getting campaigns and messages.

### ~~1.1.20~~ - Deprecated
* Added function and modified events to get klaviyo campaigns & messages

### 1.1.19
* Added bulk create events endpoint in Klaviyo client.

### 1.1.18
* Add functionality to convert dict keys to lowercase

### 1.1.17
* Disabled checking for running jobs while updating customer attributes in Klaviyo client.

### 1.1.14
* Added customer location information in Klaviyo client customer bulk update.

### 1.1.13
* Disable post-processing when updating customer attributes in Klaviyo client.

### 1.1.12
* Reduce amount of api calls made in klaviyo client during bulk update.

### 1.1.11
* Added functions to get list/segment members counts in Klaviyo client.
* Fix bug in klaviyo client where it gets stuck in a loop when getting list/segment members if list is empty.

### 1.1.10
* Added classes for trigger events and adjusted email events (get more columns) in Klaviyo client.

### 1.1.9
* Fix bug in update customer location in Klaviyo client.

### ~~1.1.8~~ - Deprecated
* Refactor bulk update method and use it when updating customer location.

### 1.1.7
* Added bulk import profile and bulk subscribe endpoints in Klaviyo client.

### 1.1.6
* Added function to get flow id using flow name (Klaviyo)

### 1.1.5
* Fixed bug when obj_to_get_from_inc is empty in get_value_from_path (Klaviyo)

### 1.1.4
* Function get_value_from_path will now return None when the field does not exist.

### 1.1.3
* Added e-mail anonymization in CRM get-related logs

### 1.1.2
* Added Klaviyo API function for deleting a customer given their email.

### 1.1.1
* Added option of including additional customer fields when getting segment members.

### 1.1.0
* Added new functionality to extract data points

### 1.0.2
* Hotfix for broken URL

### 1.0.1
* Hotfix for acceptable response codes

### 1.0
* Migrated majority of Klaviyo endpoints to work on the V3 version.

### 0.84
* Remove changes made in 0.83 and split Klaviyo timestamp on multiple tokens instead

### ~~0.83~~ - Deprecated
* Parametized the delimiter in getting next timestamp from the Klaviyo client

### 0.82
* Modify get_global_exclusions in KlaviyoClient so that we can filter based on exclusion reason or acquire all exclusions regardless of type."
* Added KlaviyoClientError class.

### 0.81
* Fixed method in KlaviyoClient for getting all the members of a list. The method should use pagination but it did not.

### 0.80 
* Fixed method in KlaviyoClient for getting global exclusions. The method was previously not using pagination which could potentially result in missing some unsubscribes.  

### 0.79
* Added function in s3 that can move objects from one bucket to another but it also has an option to only move objects that satisfy a certain condition.

### 0.78
* Fix warnings and cover corner cases in evaluate_recursively.

### 0.77
- Fix bug in KlaviyoEvent.events_to_df() so that a missing value for an event does not result in the whole dataframe missing the column.

### 0.76
- Fixed bug in KlaviyoClient.get_events() in how we paginate through the event results.
- Fixed bug in KlaviyoEvent.events_to_df() so that order of columns is preserved in the generated dataframe.

### 0.75
- Added subscription related events under klaviyo sub-module.
- Added KlaviyoClient method for getting all metrics and added an <end_ts> argument in the get_events() method, enabling to extract data from <since_ts> up to <end_ts> (i.e. extracting data for a specific time period).

### 0.74
- Bug fixes in aws secrets

### 0.73
- Added a new UDF to the utils for all functions. To be able to evaluate to python objects.
- Also added to the secrets module to evaluate all return secrets from AWS

### 0.72
- Added decorator function that posts to SNS topic if the decorated function raises an exception. 

### 0.71
- Added new functionality to CRM client to be able to post events for a metric and also use translation entries

### 0.70
- Added a new function to get secrets from AWS. https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html

### 0.69
- Added utility class for sending messages to slack.

### 0.68
- Added new function to update events in a metric for Klayiyo Client

### 0.67
- Added abstract class crm.client and made Klaviyo and Symplify clients inherit from it.
- Added metric and event class under crm.klaviyo.
- Changed typing import in parse_utils, importing OrderedDict instead of MutableMapping.

### 0.66
- Fixed issue with RotatingFileHandler appending wrong suffixes to log file names.

### ~~0.65~~ - Deprecated
- Added the RotatingFileHandler class for time-rotating logging files.

### 0.64
- Minor bug fixes to allow for package dependencies

### 0.63
- Upgraded all the packages to python 3.9 packages

### 0.62

- Added parse_utils sub-module for parsing configuration files and other text files.
- Added an execute_query method to aws.redshift.RedshiftClient for performing select statements given a string parameter.
- Making teams into a utility class instead of a client

### ~~0.61~~ - Deprecated
- Added teams client
