Expected: editing the file on GitHub would update Databricks. Happened: no change. Learned: a Git folder is a clone. You pull changes in and push changes out; nothing syncs automatically. And code stored in Git does nothing until it’s executed

Schema Drift with broker code: Broker code with inferSchema = True, taking code as integer however its string. With integer in broker file so joins to the broker reference data (stored as the string "00007") silently fail, and the data is corrupted without any error.

AUTOLOADER - i would use an autoloader with the cloudfile source on the landing folder with a checkpoint. So each file is processed exactly once as it arrives. Run with availablenow on a schedule. For a schema, autoloader stores the schema in a schema location. in addnew columnsmode, a new column Stops the stream. The schema is updated. The jobs retry picks it up. And now in the rescue mode is affected, unexpectedfields go into the rescue data column. So nothing is lost. Bronze is row, so it accepts the additive changes. Silver enforces the contract with the schema validation. If there is a type change or a dropped column, so it goes to the quarantine with an alert, and we raise it with the broker. I also add an audit column file path, ingest time from metadata .
 
- availableNow = process all new files since the checkpoint, then stop; scheduled, not event-driven. File-arrival triggers are a Jobs feature.
- schemaLocation = where Auto Loader stores the inferred schema and its versions, so it can detect and evolve changes without re-inferring.
- Schema modes: addNewColumns (update + restart), rescue (_rescued_data, schema fixed), failOnNewColumns (fail, no update), none (ignore - silent data loss).
- Checkpoint = files processed + offsets + commit log -> exactly once, even after failure.

Mode	What happens with a new column
addNewColumns (the default when you don’t supply a schema)	The schema is updated, then the stream stops; on restart it includes the new column
rescue	The schema never changes; the new column’s values go into _rescued_data (a column, not a “rescue data model”)
failOnNewColumns	The stream fails and the schema is not updated; someone must change the schema or the setup manually
none	The schema doesn’t change, the stream doesn’t fail, and the new column is ignored: the data is silently dropped unless a rescued data column is set
