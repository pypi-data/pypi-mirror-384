"""
Database executor module
Handles SQL query execution and result formatting
"""

import mysql.connector
from mysql.connector import Error
from typing import Dict
from tabulate import tabulate


def execute_query(
    sql_query: str,
    host: str,
    database: str,
    user: str,
    password: str,
    port: int = 3306
) -> Dict:
    """
    Execute SQL query on MySQL database and return results
    
    Args:
        sql_query: The SQL query to execute
        host: Database host (e.g., 'localhost' or '127.0.0.1')
        database: Database name
        user: Database username
        password: Database password
        port: Database port (default: 3306)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating if query executed successfully
        - data: List of tuples containing query results
        - columns: List of column names
        - row_count: Number of rows returned/affected
        - error: Error message if query failed
        - query_type: Type of query (SELECT, UPDATE, INSERT, DELETE)
    """
    result = {
        'success': False,
        'data': [],
        'columns': [],
        'row_count': 0,
        'error': None,
        'query_type': 'UNKNOWN'
    }
    
    connection = None
    cursor = None
    
    try:
        # Determine query type
        query_upper = sql_query.strip().upper()
        if query_upper.startswith('SELECT'):
            result['query_type'] = 'SELECT'
        elif query_upper.startswith('UPDATE'):
            result['query_type'] = 'UPDATE'
        elif query_upper.startswith('INSERT'):
            result['query_type'] = 'INSERT'
        elif query_upper.startswith('DELETE'):
            result['query_type'] = 'DELETE'
        
        # Establish database connection
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port,
            autocommit=False  # Manual commit for better control
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Execute the query
            cursor.execute(sql_query)
            
            # Handle different query types
            if result['query_type'] == 'SELECT':
                # Fetch results for SELECT queries
                result['data'] = cursor.fetchall()
                result['columns'] = [desc[0] for desc in cursor.description] if cursor.description else []
                result['row_count'] = len(result['data'])
            else:
                # For UPDATE, INSERT, DELETE queries
                result['row_count'] = cursor.rowcount
                connection.commit()  # Commit the transaction
                result['data'] = []
                result['columns'] = []
            
            result['success'] = True
            
    except Error as e:
        result['error'] = f"Database error: {str(e)}"
        result['success'] = False
        # Rollback on error
        if connection:
            connection.rollback()
        
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"
        result['success'] = False
        # Rollback on error
        if connection:
            connection.rollback()
        
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
    
    return result


def display_results(result: Dict):
    """
    Display query results in a formatted table
    
    Args:
        result: Dictionary returned from execute_query function
    """
    if not result['success']:
        print(f"❌ Query Execution Failed!")
        print(f"Error: {result['error']}\n")
        return
    
    query_type = result['query_type']
    
    # Handle SELECT queries
    if query_type == 'SELECT':
        if result['row_count'] == 0:
            print("✅ Query executed successfully!")
            print("ℹ️  No results found.\n")
            return
        
        print("✅ Query executed successfully!\n")
        print(f"📊 Results ({result['row_count']} row{'s' if result['row_count'] != 1 else ''}):")
        print("=" * 70)
        
        # Display results in a table format
        table = tabulate(
            result['data'],
            headers=result['columns'],
            tablefmt='grid',
            showindex=False
        )
        print(table)
        print("=" * 70 + "\n")
    
    # Handle UPDATE, INSERT, DELETE queries
    elif query_type in ['UPDATE', 'INSERT', 'DELETE']:
        print("✅ Query executed successfully!\n")
        
        if query_type == 'UPDATE':
            print(f"🔄 {result['row_count']} row{'s' if result['row_count'] != 1 else ''} updated.")
        elif query_type == 'INSERT':
            print(f"➕ {result['row_count']} row{'s' if result['row_count'] != 1 else ''} inserted.")
        elif query_type == 'DELETE':
            print(f"🗑️  {result['row_count']} row{'s' if result['row_count'] != 1 else ''} deleted.")
        
        print("✔️  Changes have been committed to the database.\n")
    
    # Handle unknown query types
    else:
        print("✅ Query executed successfully!\n")
        if result['row_count'] > 0:
            print(f"ℹ️  {result['row_count']} row{'s' if result['row_count'] != 1 else ''} affected.\n")
