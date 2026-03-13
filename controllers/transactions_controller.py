
from database.db_connection import getConnectionPostgreCloud

def get_all_transaction():
    conn = getConnectionPostgreCloud()
    cursor = conn.cursor()
    sql = '''select 
            transactions.transaction_id as "Transaction ID",
            accounts.account_id as "Account ID",
            accounts.account_number as "Account Number",
            transactions.amount as Amount, 
            transactions.tx_type as "Transfer Type",
            transactions.description as "Description",
            TO_CHAR(transactions.created_at, 'YYYY-MM-DD HH24:MI') as "Transfer Date"
        from transactions
        JOIN accounts ON transactions.account_id = accounts.account_id
        ORDER BY transactions.created_at DESC
        '''
    cursor.execute(sql)
    
    # Map column names to results for the HTML template
    columns = [col[0].lower() for col in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    cursor.close()
    conn.close()
    return results 


import time
from datetime import datetime
# Import your email function if it's in a different file
# from services.email_service import send_transaction_email 

def process_banking_action(account_no, amount, pin, tx_type, target_no=None):
    conn = getConnectionPostgreCloud()
    cursor = conn.cursor()
    local_now = datetime.now()
    
    try:
        # 1. Fetch Account and User Info (Matching your terminal SQL join)
        cursor.execute("""
            SELECT a.account_id, a.balance, a.transaction_pin_hash, c.customer_email, c.first_name, c.acc_username
            FROM accounts a
            JOIN customers c ON a.customer_id = c.customer_id
            WHERE a.account_number = %s
        """, (account_no,))
        
        row = cursor.fetchone()

        # 2. Match your terminal logic: Direct Comparison
        # If your terminal works with 'WHERE pin = %s', we use '==' here.
        if not row or str(row[2]) != str(pin):
            return False, "Invalid Account or PIN"

        acc_id, current_balance, db_pin, email, first_name, username = row
        amount = float(amount)

        # 3. Check Balance for Withdraw/Transfer
        if tx_type in ['withdraw', 'transfer'] and current_balance < amount:
            return False, "Insufficient Funds"

        # 4. Perform Database Updates
        if tx_type == 'deposit':
            cursor.execute("UPDATE accounts SET balance = balance + %s WHERE account_id = %s", (amount, acc_id))
        elif tx_type == 'withdraw':
            cursor.execute("UPDATE accounts SET balance = balance - %s WHERE account_id = %s", (amount, acc_id))
        elif tx_type == 'transfer':
            cursor.execute("UPDATE accounts SET balance = balance - %s WHERE account_id = %s", (amount, acc_id))
            cursor.execute("UPDATE accounts SET balance = balance + %s WHERE account_number = %s", (amount, target_no))
        elif tx_type == "transfer" and not target_no:
            return False, "Target account required"

        # 5. Insert Transaction Log
        # 5. Insert Transaction Log
        cursor.execute("""
            INSERT INTO transactions (account_id, amount, tx_type, description, created_at) 
            VALUES (%s, %s, %s, %s, %s) 
            RETURNING transaction_id
        """, (acc_id, amount, tx_type.capitalize(), f"{tx_type.capitalize()} {account_no}", local_now))

        # IMPORTANT: You must fetch the ID right here!
        result = cursor.fetchone()
        if result:
            new_id = result[0]
        else:
            raise Exception("Failed to retrieve Transaction ID")

        conn.commit()
        return True, new_id  # Send the ID back to app.py

    except Exception as e:
        conn.rollback()
        return False, f"Database Error: {str(e)}"
    finally:
        cursor.close()
        conn.close()



