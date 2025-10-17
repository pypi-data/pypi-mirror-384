from abc import ABC, abstractmethod
import dlt
import polars as pl
from pathlib import Path


class BaseLoader(ABC):
    def __init__(self, duckdb_path: Path):
        self.destination = dlt.destinations.duckdb(duckdb_path)
        duckdb_path.parent.mkdir(parents=True, exist_ok=True)

    def load_dataframe(
        self,
        df: pl.DataFrame,
        schema: str,
        table: str,
        write_disposition: str = "append",
        **kwargs,
    ) -> Path:
        # Convert DataFrame to list of dicts for DLT
        data = df.to_dicts()

        # Create a DLT resource from the data
        resource = dlt.resource(data, name=table)
        if kwargs.get("apply_hints"):
            resource.apply_hints(kwargs["apply_hints"])

        # Create pipeline with destination-specific configuration
        pipeline = dlt.pipeline(
            pipeline_name="dataframe_loader",
            destination=self.destination,
            dataset_name=schema,
        )

        # Load data
        result = pipeline.run(
            resource,
            table_name=table,
            write_disposition=write_disposition,
        )

        return result
