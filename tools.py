import sqlite3

def get_db_schema():
    try:
        conn = sqlite3.connect('chinook.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        schema = {}
        for (table_name,) in tables:
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            schema[table_name] = [{
                'cid': col[0], 'name': col[1], 'type': col[2], 'notnull': col[3], 'default': col[4], 'pk': col[5]
            } for col in columns]
        conn.close()
        return schema
    except Exception as e:
        return f"Error getting schema: {e}"

def explore_db_schema():
    try:
        conn = sqlite3.connect('chinook.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        schema_details = []
        for (table_name,) in tables:
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            schema_details.append({
                'table': table_name,
                'columns': [{
                    'name': col[1], 'type': col[2], 'notnull': col[3], 'default': col[4], 'pk': col[5]
                } for col in columns]
            })
        conn.close()
        return {
            'tables': len(tables),
            'details': schema_details
        }
    except Exception as e:
        return f"Error exploring schema: {e}"

def query_database(query):
    try:
        conn = sqlite3.connect('chinook.db')
        cursor = conn.cursor()
        cursor.execute(query)
        if query.strip().lower().startswith('select'):
            rows = cursor.fetchall()
            result = rows
        else:
            conn.commit()
            result = f"Query executed successfully."
        conn.close()
        return result
    except Exception as e:
        return f"Error executing query: {e}"

def summarize_database():
    try:
        conn = sqlite3.connect('chinook.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        summary = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            cursor.execute(f"SELECT * FROM {table} LIMIT 3")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            summary[table] = {
                'row_count': count,
                'sample_rows': [dict(zip(columns, row)) for row in rows]
            }
        conn.close()
        return summary
    except Exception as e:
        return f"Error summarizing database: {e}"
