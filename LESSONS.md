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



Expected: all six Bronze streams to start. Happened: claim_events failed with CF_EMPTY_DIR_FOR_SCHEMA_INFERENCE. Day 1–2 claim files were 0 bytes, because no claims had been reported yet. Learned: Auto Loader needs data (or an explicit schema) to infer a schema the first time. I added a guard that skips a source until it has data. Real feeds send empty files, so the pipeline has to handle them.


why did it fail first, then work? Because of schema drift, a new column "Payment method" is added, with schemaEvolution is addNewColumns mode, autoloader updates the schema in schema location , then stops the streams so new schema is picked up on restart. In production, job's retry handles this automatically. Day-1 to Day-9 , payment method is blank. for those days, payment method was not there earlier. 

- Re-run with no new files: 0 rows. The checkpoint already recorded those files -> idempotent, exactly-once.
- _rescued_data = data that doesn't fit the schema (rescue-mode new columns, type mismatches, malformed fields). With addNewColumns + all-string Bronze, mine has 0 rows: the new column became a real column.
- One checkpoint per stream: it holds that stream's files, offsets and commits. Sharing would corrupt progress; separate checkpoints let me replay one source alone.
- Delta enforces schema by default (rejects new columns). mergeSchema=true allows evolution on the table; addNewColumns evolves the stream's schema. Need both.

Expected: Bronze = 31,924 rows (source of truth). Happened: 30,775. A file-by-file reconciliation showed premium_bordereau_20260116.csv had 1,149 raw rows and 0 in Bronze. Day 16 was never landed (off-by-one in range()). Every run was green. Learned: green ≠ complete. Reconcile at file level, and add a missing-file completeness check.


Why are Bronze columns strings? Where does typing happen? => Bronze is raw layer, no bad records. everything can be appended and replayable. Typping happen in silver layer where if datatype does not match, store in quartine table .

What happened when you deleted the checkpoint, and how do you protect against it in production?
checkpoints on restricted storage: only the job’s service principal can write or delete them, not people. never share, move or casually delete a checkpoint; a reset is a deliberate, reviewed action. idempotent Silver (MERGE on the business key) as a safety net, so a replay can’t create duplicates downstream. row-count reconciliation to catch a doubling immediately

How would you detect a late-arriving file, and how would you detect a missing one (like your day 16)?
Compare the business date with the ingest date.
expect one file per source per business day; if it hasn’t arrived by the cut-off time, alert

Why do duplicates stay in Bronze
Bronze is a faithful record of exactly what the source sent. Duplicates are evidence: if a broker sends a line twice, I want to be able to prove it. Bronze also has to be replayable. Dedup belongs in Silver, where the business key is known


foreachBatch -  what does it let you do inside a stream that a plain writeStream.toTable can't?
it lets you treat each micro-batch of streaming data as a normal batch DataFrame and execute custom logic on it. But the write itself is relatively straightforward. It doesn't provide a callback where you can run arbitrary batch logic for every micro-batch.
With foreachBatch, Spark gives you two things for every micro-batch:
- batch_df → the DataFrame containing the current batch of records.
- batch_id → the unique ID of that micro-batch within the streaming query.

try_cast vs cast - what's the difference when the value is "abc"?

try_cast - Instead of throwing an error for an invalid value, TRY_CAST returns NULL, allowing the pipeline to continue processing other records.

CAST attempts to convert the value into the target type. Since "abc" is not a valid integer, the conversion fails and can cause your query to error

Error vs warning severity - why have both? 
If whole job flow can fail with bad record then severity should be error and stored in quarartine table. 

If it's not going to cause any fail then add in silver tabler with warning. 

Reject threshold - why fail the whole batch if, say, more than 1% of rows are bad?
1% of the rows are bad for a batch processing. It means file is not good enough to process . batch fail with an alert is important to have on data quality side.

Idempotent - what makes a Silver write safe to re-run?

In case of job failure, with retrial, duplicate data should not be stored in silver layer. In silver layer, handle de-dup and merge query makes it idempotent. 