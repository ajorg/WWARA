# WWARA
Some scripts to convert data from [WWARA](https://www.wwara.org/) to other useful formats

## `wwara-repeaterbook`

Compares RepeaterBook's data against authoritative data from WWARA.

### Attrubtion [sic]

This product uses RepeaterBook Data API but is not endorsed or certified by RepeaterBook

## `wwara.delta`

AWS Lambda function
using S3 versioning
and events
to compare the previous database extract
to the latest
and send a notification through SNS.

```
zip -9 delta.zip wwara/delta.py wwara/database.py wwara/plan.py wwara/qa.py channel.py rule.py
```
