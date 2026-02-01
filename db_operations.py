import mysql.connector
from mysql.connector import Error

def insert_transaction(user_id, product_id, quantity, price,transaction_time,category_id=None,description=None):
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='live_data_project', 
            user='root',         
            password='root'  
        )
        if connection.is_connected():
            cursor = connection.cursor()
            sql = """
                INSERT INTO transactions (user_id, product_id, quantity, price, transaction_time)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    quantity = VALUES(quantity),
                    price = VALUES(price)
            """

  
            cursor.execute(sql, (user_id, product_id, quantity, price, transaction_time))
            connection.commit()
            print(f"Transaction inserted successfully: user={user_id}, product={product_id}")
    except Error as e:
        print("Error while connecting to MySQL:", e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
