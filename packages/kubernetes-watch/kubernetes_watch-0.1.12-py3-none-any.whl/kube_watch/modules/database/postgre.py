import psycopg2
import psycopg2.extras
from prefect import get_run_logger

from .model import TableQuery

logger = get_run_logger()


def execute_query(db_user, db_pass, db_query, db_host="localhost", db_port=5432, db_name="postgres"):
    """
    Connect to PostgreSQL database, execute a query, and return status message.
    
    Args:
        db_user (str): Database username
        db_pass (str): Database password
        db_query (str): SQL query to execute
        db_host (str): Database host (default: localhost)
        db_port (int): Database port (default: 5432)
        db_name (str): Database name (default: postgres)
    
    Returns:
        dict: Status message with success/failure information
    """
    connection = None
    cursor = None
    
    try:
        # Establish database connection
        connection = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_pass
        )
        
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Execute the query
        cursor.execute(db_query)
        
        # Check if it's a SELECT query to fetch results
        if db_query.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
            row_count = len(results)
            connection.commit()  # Commit even for SELECT to close transaction
            
            logger.info(f"Query executed successfully. Retrieved {row_count} rows.")
            return {
                "status": "success",
                "message": f"Query executed successfully. Retrieved {row_count} rows.",
                "row_count": row_count,
                "data": results
            }
        else:
            # For INSERT, UPDATE, DELETE queries
            connection.commit()
            affected_rows = cursor.rowcount
            
            logger.info(f"Query executed successfully. {affected_rows} rows affected.")
            return {
                "status": "success",
                "message": f"Query executed successfully. {affected_rows} rows affected.",
                "affected_rows": affected_rows
            }
            
    except psycopg2.Error as e:
        # PostgreSQL specific errors
        error_msg = f"PostgreSQL error: {str(e)}"
        logger.error(error_msg)
        
        if connection:
            connection.rollback()
            
        return {
            "status": "error",
            "message": error_msg,
            "error_type": "postgresql_error"
        }
        
    except Exception as e:
        # General errors
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        
        if connection:
            connection.rollback()
            
        return {
            "status": "error", 
            "message": error_msg,
            "error_type": "general_error"
        }
        
    finally:
        # Clean up connections
        try:
            if cursor:
                cursor.close()
                logger.debug("Database cursor closed.")
                
            if connection:
                connection.close()
                logger.debug("Database connection closed.")
                
        except Exception as cleanup_error:
            logger.warning(f"Error during cleanup: {str(cleanup_error)}")


def delete_on_retention_period(table_delete: dict, batch_size: int = 100000, interval_days: int = 14):
    """
    Delete rows older than a specified retention period from a table in PostgreSQL.

    Args:
        table_delete (dict[TableQuery]): Object containing table name and column name.
        batch_size (int): Number of rows to delete in each batch (default: 100000).
        interval_days (int): Retention period in days (default: 14).

    Returns:
        dict: Status message with success/failure information.
    """

    try:
        table_query = TableQuery(**table_delete)
    except Exception as e:
        logger.error(f"Error creating TableQuery object: {str(e)}")
        raise ValueError("Invalid table_delete data format. Expected a dictionary with 'name', 'column_name', 'db_host', 'db_port', 'db_name', 'db_user', and 'db_pass' keys.")

    connection = None
    cursor = None

    try:
        # Establish database connection
        connection = psycopg2.connect(
            host=table_query.db_host,
            port=table_query.db_port,
            database=table_query.db_name,
            user=table_query.db_user,
            password=table_query.db_pass
        )

        cursor = connection.cursor()

        rows_deleted_total = 0

        while True:
            # Build the DELETE query dynamically
            delete_query = f"""
            DELETE FROM {table_query.table_name}
            WHERE id IN (
                SELECT id FROM {table_query.table_name}
                WHERE {table_query.column_name} < NOW() - INTERVAL '{interval_days} days'
                LIMIT {batch_size}
            )
            """

            cursor.execute(delete_query)
            rows_deleted = cursor.rowcount
            rows_deleted_total += rows_deleted

            connection.commit()

            logger.info(f"Deleted {rows_deleted} rows from {table_query.table_name}.")

            # Exit the loop if no rows were deleted
            if rows_deleted == 0:
                break

        logger.info(f"Total rows deleted from {table_query.table_name}: {rows_deleted_total}.")

        return {
            "status": "success",
            "message": f"Total rows deleted from {table_query.table_name}: {rows_deleted_total}.",
            "rows_deleted_total": rows_deleted_total
        }

    except psycopg2.Error as e:
        error_msg = f"PostgreSQL error: {str(e)}"
        logger.error(error_msg)

        if connection:
            connection.rollback()

        return {
            "status": "error",
            "message": error_msg,
            "error_type": "postgresql_error"
        }

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)

        if connection:
            connection.rollback()

        return {
            "status": "error",
            "message": error_msg,
            "error_type": "general_error"
        }

    finally:
        # Clean up connections
        try:
            if cursor:
                cursor.close()
                logger.debug("Database cursor closed.")

            if connection:
                connection.close()
                logger.debug("Database connection closed.")

        except Exception as cleanup_error:
            logger.warning(f"Error during cleanup: {str(cleanup_error)}")

"""
EXAMPLE RETENTION PERIOD DELETION QUERY

DO $$
DECLARE
    batch_size INTEGER := 100000;
    rows_deleted INTEGER;
    t TEXT;
    col TEXT;
    sql TEXT;
    count_sql TEXT;

    -- Define loop record
    rec RECORD;
BEGIN
    -- Simulate table/column pairs using VALUES
    FOR rec IN
        SELECT * FROM (
            VALUES
                ('log', 'created'),
                ('task_run_state', 'timestamp'),
                ('task_run', 'start_time'),
                ('flow_run_state', 'timestamp'),
                ('flow_run', 'start_time')
        ) AS table_info(table_name, column_name)
    LOOP
        t := rec.table_name;
        col := rec.column_name;

        LOOP
            sql := format(
                'DELETE FROM %I WHERE id IN (
                    SELECT id FROM %I WHERE %I < NOW() - INTERVAL ''14 days'' LIMIT %s
                )',
                t, t, col, batch_size
            );

            EXECUTE sql;
            GET DIAGNOSTICS rows_deleted = ROW_COUNT;

            RAISE NOTICE 'Deleted % rows from %', rows_deleted, t;
            EXIT WHEN rows_deleted = 0;
        END LOOP;

        count_sql := format(
            'SELECT COUNT(*) FROM %I WHERE %I < NOW() - INTERVAL ''14 days''',
            t, col
        );

        EXECUTE count_sql INTO rows_deleted;
        RAISE NOTICE 'Remaining rows in % older than 14 days: %', t, rows_deleted;
    END LOOP;
END $$;
"""