-- 1. Catalog for the dev environment
CREATE CATALOG IF NOT EXISTS dev_insurance
  COMMENT 'Motor insurance lakehouse - dev';
-- If CREATE CATALOG is not allowed in your edition, use the default `workspace` catalog
-- and replace dev_insurance with workspace everywhere below. Note it in LESSONS.md.

USE CATALOG dev_insurance;

-- 2. Schemas: one per layer, plus landing and ops
CREATE SCHEMA IF NOT EXISTS landing COMMENT 'Raw files as delivered by sources';
CREATE SCHEMA IF NOT EXISTS bronze  COMMENT 'Raw, append-only, with audit columns';
CREATE SCHEMA IF NOT EXISTS silver  COMMENT 'Typed, deduplicated, validated, SCD2 history';
CREATE SCHEMA IF NOT EXISTS gold    COMMENT 'Dimensional model and KPIs';
CREATE SCHEMA IF NOT EXISTS ops     COMMENT 'Control, DQ results, reconciliation, checkpoints';

-- 3. Volumes (governed file storage)
CREATE VOLUME IF NOT EXISTS landing.raw        COMMENT 'Source files land here';
CREATE VOLUME IF NOT EXISTS ops.checkpoints    COMMENT 'Streaming checkpoints';
CREATE VOLUME IF NOT EXISTS ops.schemas        COMMENT 'Auto Loader schema locations';

-- 4. Check
SHOW SCHEMAS IN dev_insurance;
SHOW VOLUMES IN dev_insurance.landing;


