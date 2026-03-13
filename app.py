from flask import Flask, make_response , render_template, request, redirect, url_for # Added url_for
from controllers.transactions_controller import get_all_transaction, process_banking_action
from database.db_connection import getConnectionPostgreCloud

app = Flask(__name__)

# Run table creation on startup
# create_product_table()

@app.route('/', methods=['GET', 'POST'])
def execute_tx():
    if request.method == 'POST':
        # Extracting data from the form to pass to the controller
        account_no = request.form.get('account_number')
        amount = request.form.get('amount')
        pin = request.form.get('pin')
        tx_type = request.form.get('tx_type')
        target_no = request.form.get('target_account_number') 

        success, result_val = process_banking_action(account_no, amount, pin, tx_type, target_no)
    
        if success:
            # result_val is the ID (e.g., 105)
            return redirect(url_for('show_invoice', tx_id=result_val))
        else:
            # result_val is the error string
            return f"<h3>Transaction Failed: {result_val}</h3><a href='/'>Try Again</a>"
    
    response = make_response(render_template('transactionsPage.html'))
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.route('/transactions')
def show_all_transactions():
    data = get_all_transaction()
    return render_template('transactionsPage.html', history=data)


@app.route('/invoice/<int:tx_id>')
def show_invoice(tx_id):
    conn = getConnectionPostgreCloud()
    cursor = conn.cursor()
    # Fetch details to show on the receipt
    cursor.execute("""
        SELECT t.transaction_id, t.amount, t.tx_type, t.created_at, a.account_number 
        FROM transactions t 
        JOIN accounts a ON t.account_id = a.account_id 
        WHERE t.transaction_id = %s
    """, (tx_id,))
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return render_template('invoicePage.html', tx=data)

@app.route('/check_account', methods=['POST'])
def check_account():
    data = request.get_json()
    acc_no = data.get("account_number")

    conn = getConnectionPostgreCloud()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.acc_username
        FROM accounts a
        JOIN customers c ON a.customer_id = c.customer_id
        WHERE a.account_number = %s
    """, (acc_no,))

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row:
        return {"success": True, "name": row[0]}
    else:
        return {"success": False}

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store"
    return response

if __name__ == "__main__":
    app.run(debug=True)