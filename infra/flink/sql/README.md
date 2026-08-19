# Flink SQL streaming (scaffold)

The functional streaming pipeline ships as Python services:
`stream-producer` (faker -> Redpanda topic `users`) and `stream-consumer`
(Redpanda -> Iceberg bronze.users_stream via PyIceberg + Trino register_table).

To use the native Flink SQL path instead, build a Flink image that includes the
Iceberg Flink runtime, flink-connector-kafka and the S3/hadoop plugins, then:
  ./bin/sql-client.sh -f 01_iceberg_catalog.sql -f 02_source_sink.sql
