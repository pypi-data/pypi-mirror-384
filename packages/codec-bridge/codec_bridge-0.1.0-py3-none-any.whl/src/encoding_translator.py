import charset_normalizer
import os
import re

from repository.python_to_duckdb import PYTHON_TO_DUCKDB_ENCODING, ENCODINGS_UNDERSCORE_CONFLICT


def get_duckdb_encoding(python_encoding_name: str) -> str:
    """
    Translates a Python-standard encoding name to the name expected by DuckDB.
    If no specific mapping is found, it returns the original name as a fallback.

    :param python_encoding_name: The encoding name detected (e.g., 'iso-8859-1').
    :return: The translated encoding name for DuckDB (e.g., 'ibm-819').
    """
    if not python_encoding_name:
        return 'utf-8'

    normalized_name = python_encoding_name.lower()
    return PYTHON_TO_DUCKDB_ENCODING.get(normalized_name, python_encoding_name)


def detect_encoding(file_path: str, chunk: int = 1000000) -> str:
    """
    Detects the character encoding of a file using charset_normalizer.

    :param file_path: The full path to the file.
    :return: The detected encoding name as a string.
    """
    with open(file_path, "rb") as file:
        data_sample = file.read(chunk)
        result = charset_normalizer.detect(data_sample)
        return result.get("encoding") if result else "utf-8"

def detect_delimiter(file_path: str, encoding: str = "utf-8") -> str:
    """
    Detects the most likely delimiter based on the first line of the file.

    :param file_path: The full path to the file.
    :param encoding: The encoding to use when reading the file.
    :return: The detected delimiter character.
    """
    possible_delimiters = [',', ';', '\t', '|']
    detected_delimiter = ','  # Default to comma
    if encoding.lower() in ENCODINGS_UNDERSCORE_CONFLICT:
        return '|'
    try:
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            first_line = f.readline()
            # Find the delimiter with the highest count in the header line
            counts = {d: first_line.count(d) for d in possible_delimiters}
            if any(c > 0 for c in counts.values()):
                detected_delimiter = max(counts, key=counts.get)
    except Exception as e:
        print(f"[WARN] Could not detect delimiter for {os.path.basename(file_path)}: {e}")

    return detected_delimiter

def process_files(directory_path: str) -> list[dict]:
    """
    Iterates through all CSV files in the instance's directory, detects their
    properties (encoding, delimiter), and stores them as metadata.

    This method acts as a utility to scan and prepare a batch of files.

    :return: A list of dictionaries, each containing metadata for a file.
    """
    if not os.path.isdir(directory_path):
        print(f"Error: The directory '{directory_path}' does not exist.")
        return []

    results = []
    for filename in os.listdir(directory_path):
        if not filename.lower().endswith('.csv'):
            continue

        file_path = os.path.join(directory_path, filename)

        # Detect properties
        python_encoding = detect_encoding(file_path)
        delimiter = detect_delimiter(file_path, encoding=python_encoding)

        # Translate encoding for the target enconding case
        duckdb_encoding = get_duckdb_encoding(python_encoding)

        # Sanitize filename to create a valid table name
        table_name = re.sub(r'[^a-zA-Z0-9_]', '_', os.path.splitext(filename)[0])

        results.append({
            "filename": filename,
            "path": file_path,
            "python_encoding": python_encoding,
            "duckdb_encoding": duckdb_encoding,
            "delimiter": delimiter,
            "table_name": table_name
        })

    return results

def write_utf8_csv(file_path: str, new_csv_file_path: str):

    """
    Rewrites a CSV file using UTF-8 encoding.

    This method is intended for cases where, even after DuckDB's encoding detection,
    the file is still incorrectly interpreted when inserted into the database.

    :param file_path: Path to the original CSV file.
    :param new_csv_file_path: Path where the UTF-8 encoded CSV will be saved.
    :return: None. The UTF-8 encoded file is written to disk.
    """
    with open(file_path, 'r') as file:
        with open(new_csv_file_path, 'w', encoding='utf-8') as new_file:
            for line in file:
                new_file.write(line)

if __name__ == "__main__":
    import duckdb
    from tests.duckdb_utils import create_table_from_csv

    csv_directory_path = "//tests/assets/"

    connection = duckdb.connect(database=":memory:")

    connection.execute("INSTALL encodings")
    connection.execute("LOAD encodings")

    detector = get_duckdb_encoding(csv_directory_path)

    file_results = process_files(csv_directory_path)

    for result in file_results:
        create_table_from_csv(
            conn=connection,
            file_path=result["path"],
            table_name=result["table_name"],
            delimiter=result["delimiter"],
            encoding=result["duckdb_encoding"]
        )

    connection.close()