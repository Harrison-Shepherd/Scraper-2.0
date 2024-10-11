from SqlConnector import connect  

def drop_all_tables(connection):
    """Drop all tables from the current database, including those with foreign key constraints."""
    try:
        cursor = connection.cursor()

        # Disable foreign key checks before dropping the tables
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        print("Foreign key checks disabled.")

        # Query to get all table names
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()

        # Drop each table
        for table in tables:
            drop_table_query = f"DROP TABLE IF EXISTS `{table[0]}`;"
            cursor.execute(drop_table_query)
            print(f"Dropped table: {table[0]}")

        # Re-enable foreign key checks after dropping the tables
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        print("Foreign key checks enabled.")

        connection.commit()
        cursor.close()
        print("Successfully dropped all tables.")
    except Exception as e:
        print(f"Error dropping tables: {e}")

if __name__ == "__main__":
    # Use the connect function from SqlConnector to establish the connection
    connection = connect()

    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("USE `PowerData`;")  
            print("Connected to PowerData database.")
            cursor.close()

            # Call the function to drop all tables
            drop_all_tables(connection)

        except Exception as e:
            print(f"Error selecting database: {e}")
        finally:
            connection.close()
    else:
        print("Failed to connect to the database.")
