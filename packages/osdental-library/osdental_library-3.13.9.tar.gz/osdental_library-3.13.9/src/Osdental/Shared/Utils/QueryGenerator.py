 
class QueryGenerator:

    @staticmethod
    def generate(schema_name: str, table_name: str, data: dict[str, str] = None) -> str:
        query = f"EXEC {schema_name}.{table_name}"
 
        if data is not None:
            for key in data.keys():
                query += f"\n@i_{key} = :{key},"
            query = query[:-1]
 
        return query