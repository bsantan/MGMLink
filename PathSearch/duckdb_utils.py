# Code to form duckdb queries using python

def get_table_count(con, table):
    """Get the number of rows of a given duckdb table name."""
    # Execute the SQL query to count the rows
    result = con.execute(
        f"""
        SELECT COUNT(*) FROM "{table}";
    """
    ).fetchone()

    # Print the number of rows
    print(f"Number of rows in '{table}': {result[0]}")

    return result[0]

def duckdb_load_table(con, file, table_name, columns):
    """Create a duckDB tables for any given graph."""
    columns_str = ", ".join(columns)

    # Read the subset file into a DuckDB table
    query = (
        f"""
    CREATE OR REPLACE TABLE {table_name} AS
    SELECT {columns_str}
    FROM read_csv_auto('{file}', delim='\t');
    """
    )

    # print(query)
    con.execute(query)

    # Remove brackets
    remove_character_from_table(
            con,
            table_name = "edges",
            symbol = "<|>",
            column_name = "subject"
        )
    remove_character_from_table(
            con,
            table_name = "edges",
            symbol = "<|>",
            column_name = "predicate"
        )
    remove_character_from_table(
            con,
            table_name = "edges",
            symbol = "<|>",
            column_name = "object"
        )

def create_subject_object_pair_table(con, table_name, base_table_name, subject, object, subject_prefix, predicate_prefix, object_prefix):

    query = (
        f"""
        CREATE TEMPORARY TABLE "{table_name}" AS
        SELECT DISTINCT subject AS "{subject}", predicate, object AS "{object}"
        FROM "{base_table_name}"
        WHERE subject LIKE '{subject_prefix}' AND predicate LIKE '{predicate_prefix}' AND object LIKE '{object_prefix}';
        """
    )

    # print(query)
    con.execute(query).fetchone()

    return table_name

def join_tables_subject_object(con, base_table_name, compared_table_name, output_table_name, output_subject, output_object, comparison):

    query = (
        f"""
        CREATE TEMPORARY TABLE "{output_table_name}" AS
        SELECT DISTINCT "{compared_table_name}"."{output_subject}", "{compared_table_name}".predicate, "{compared_table_name}"."{comparison}", "{base_table_name}".predicate, "{base_table_name}"."{output_object}"
        FROM "{base_table_name}"
        JOIN "{compared_table_name}" ON "{base_table_name}"."{comparison}" = "{compared_table_name}"."{comparison}"
        WHERE "{compared_table_name}"."{output_subject}" != "{base_table_name}"."{output_object}";

        DROP TABLE "{compared_table_name}";
        """
    )

    # print(query)
    con.execute(query)

def create_filtered_subject_object_pair_table(con, base_table_name, compared_table_name, output_table_name, subject, object, subject_prefix, predicate_prefix, object_prefix):

    query = (
        f"""
        CREATE TEMPORARY TABLE "{output_table_name}" AS
        SELECT DISTINCT e.subject AS "{subject}", e.predicate, e.object AS "{object}"
        FROM "{base_table_name}" e
        WHERE e.subject IN (SELECT "{subject}" FROM "{compared_table_name}")
        AND e.subject LIKE '{subject_prefix}' AND e.predicate LIKE '{predicate_prefix}' AND e.object LIKE '{object_prefix}';
        """
    )

    # print(query)
    con.execute(query)

    return output_table_name

def remove_character_from_table(con,table_name,symbol,column_name):

    query = (
        f"""
        UPDATE '{table_name}'
        SET 
            {column_name} = REPLACE(REPLACE({column_name}, '<', ''), '>', '');
        """
    )

    # print(query)
    con.execute(query)

def drop_table(con, table_name):

    query = (
        f"""
        DROP TABLE "{table_name}";
        """
    )

    # print(query)
    con.execute(query)
    # print("dropped ",table_name)

def output_table_to_file(con, table_name, filename):

    query = (
        f"""
        COPY {table_name} TO '{filename}' (FORMAT CSV, DELIMITER '\t', HEADER);
        """
    ) 

    # print(query)
    con.execute(query)