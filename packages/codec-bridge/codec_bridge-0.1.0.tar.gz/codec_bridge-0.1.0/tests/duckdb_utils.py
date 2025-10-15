import os
def create_table_from_csv(conn, file_path: str, table_name: str, delimiter: str = '|', encoding: str = "utf-8"):
    """
    Create a table on DuckDB
    """
    print(f"Processando '{os.path.basename(file_path)}': Tabela='{table_name}', Encoding='{encoding}', Delim='{delimiter}'")
    try:
        conn.sql(f"""
                CREATE OR REPLACE TEMP TABLE "{table_name}" AS
                (SELECT * FROM 
                read_csv('{file_path}',
                delim='{delimiter}',
                encoding='{encoding}',
                header=true,
                auto_detect=true
                ) LIMIT 1000)
                """)
        print(f"✅ Tabela '{table_name}' criada com sucesso.")
        print(conn.sql(f'SELECT * FROM "{table_name}" LIMIT 3'))
    except Exception as e:
        print(f"❌ ERRO ao criar a tabela '{table_name}': {e}")