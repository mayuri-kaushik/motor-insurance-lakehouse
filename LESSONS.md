Expected: editing the file on GitHub would update Databricks. Happened: no change. Learned: a Git folder is a clone. You pull changes in and push changes out; nothing syncs automatically. And code stored in Git does nothing until it’s executed

Schema Drift with broker code: Broker code with inferSchema = True, taking code as integer however its string. With integer in broker file so joins to the broker reference data (stored as the string "00007") silently fail, and the data is corrupted without any error.

 cloudFiles source – what does it do that spark.read.csv(folder) doesn't?
 Checkpoint – what's stored there?
 schemaLocation – why does Auto Loader save the schema?
 schemaEvolutionMode: addNewColumns vs rescue vs failOnNewColumns vs none
 trigger(availableNow=True) – why is it a good fit for daily files?
 


