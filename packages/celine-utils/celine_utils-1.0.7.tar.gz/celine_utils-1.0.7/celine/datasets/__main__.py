from . import DatasetClient
import json


def main():
    client = DatasetClient()

    # List schemas and tables
    schemas = client.get_database_schemas()
    print("Schemas and tables:", json.dumps(schemas, indent=4))

    # Example: pick the first schema + table
    if schemas:
        schema, tables = next(iter(schemas.items()))
        table = tables[0]
        print(f"\nInspecting {schema}.{table}...")

        # Get table structure
        structure = client.get_table_structure(schema, table)
        print("Structure:", json.dumps(structure, indent=4))

        # Get model and fetch rows
        model = client.get_model(schema, table)
        df = (
            client.select(schema, table)
            # .where(model.c.something == "active")
            .limit(10).to_dataframe()
        )
        print(df)
    else:
        print("No tables found in database.")


if __name__ == "__main__":
    main()
