-- Flink SQL: Iceberg catalog over MinIO (hadoop catalog).
-- Requires the Iceberg Flink runtime + Flink S3/Hadoop plugins in the Flink image.
-- Submit with: ./bin/sql-client.sh -f sql/01_iceberg_catalog.sql -f sql/02_source_sink.sql
CREATE CATALOG iceberg_catalog WITH (
  'type' = 'iceberg',
  'catalog-type' = 'hadoop',
  'warehouse' = 's3://warehouse',
  'property-version' = '1'
);

CREATE DATABASE IF NOT EXISTS iceberg_catalog.bronze;
