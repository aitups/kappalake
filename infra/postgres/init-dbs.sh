#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE dagster;
    CREATE DATABASE keycloak;
    GRANT ALL PRIVILEGES ON DATABASE dagster TO admin;
    GRANT ALL PRIVILEGES ON DATABASE keycloak TO admin;

    -- Iceberg JDBC Catalog Tables
    CREATE TABLE IF NOT EXISTS iceberg_tables (
        catalog_name VARCHAR(255) NOT NULL,
        table_namespace VARCHAR(255) NOT NULL,
        table_name VARCHAR(255) NOT NULL,
        metadata_location VARCHAR(1000),
        previous_metadata_location VARCHAR(1000),
        PRIMARY KEY (catalog_name, table_namespace, table_name)
    );

    CREATE TABLE IF NOT EXISTS iceberg_namespace_properties (
        catalog_name VARCHAR(255) NOT NULL,
        namespace VARCHAR(255) NOT NULL,
        property_key VARCHAR(255) NOT NULL,
        property_value VARCHAR(1000),
        PRIMARY KEY (catalog_name, namespace, property_key)
    );
EOSQL
