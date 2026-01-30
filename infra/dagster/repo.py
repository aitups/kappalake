from dagster import asset, repository, Definitions
import airbyte as ab

@asset
def faker_users_bronze():
    """
    Ingests fake user data using Airbyte (source-faker) and loads it into a local cache (DuckDB).
    In a real scenario, we would configure the destination to be S3/MinIO (Iceberg).
    """
    # Create the source connector
    source = ab.get_source(
        "source-faker",
        config={"count": 100, "seed": 123},
        install_if_missing=True,
    )
    
    # Verify connection
    source.check()
    
    # Select the 'users' stream
    source.select_streams(["users"])

    # Read data into cache (defaulting to local DuckDB for simplicity in this MVP)
    # This automatically runs the Airbyte sync
    cache = ab.get_default_cache()
    result = source.read(cache=cache)
    
    # Return some metadata about what we just ingested
    df = result["users"].to_pandas()
    return {
        "num_rows": len(df),
        "columns": list(df.columns),
        "sample": df.head(5).to_dict()
    }

@repository
def kappalake_repo():
    return [faker_users_bronze]
