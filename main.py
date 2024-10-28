from flask import Flask, request, jsonify, render_template_string
from circle.sdk import Circle
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Circle SDK
circle = Circle(
    api_key=os.getenv('CIRCLE_API_KEY'),
    api_url=os.getenv('CIRCLE_API_URL')
)

# HTML template for the payment form
PAYMENT_FORM = '''
<!DOCTYPE html>
<html>
<head>
    <title>Circle Payment Demo</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input { width: 100%; padding: 8px; margin-bottom: 10px; }
        button { background-color: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; }
        button:hover { background-color: #45a049; }
    </style>
</head>
<body>
    <h1>Make a Payment</h1>
    <form id="paymentForm" onsubmit="handleSubmit(event)">
        <div class="form-group">
            <label for="amount">Amount (USD):</label>
            <input type="number" id="amount" name="amount" required min="1" step="0.01">
        </div>
        <div class="form-group">
            <label for="cardNumber">Card Number:</label>
            <input type="text" id="cardNumber" name="cardNumber" required>
        </div>
        <div class="form-group">
            <label for="expMonth">Expiration Month:</label>
            <input type="number" id="expMonth" name="expMonth" required min="1" max="12">
        </div>
        <div class="form-group">
            <label for="expYear">Expiration Year:</label>
            <input type="number" id="expYear" name="expYear" required min="2024">
        </div>
        <div class="form-group">
            <label for="cvv">CVV:</label>
            <input type="text" id="cvv" name="cvv" required>
        </div>
        <button type="submit">Submit Payment</button>
    </form>
    <div id="result"></div>

    <script>
        async function handleSubmit(event) {
            event.preventDefault();
            const formData = new FormData(event.target);
            const data = Object.fromEntries(formData.entries());
            
            try {
                const response = await fetch('/process-payment', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                document.getElementById('result').innerHTML = 
                    `<p style="color: ${result.success ? 'green' : 'red'}">
                        ${result.message}
                    </p>`;
            } catch (error) {
                document.getElementById('result').innerHTML = 
                    `<p style="color: red">Error processing payment: ${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(PAYMENT_FORM)

@app.route('/process-payment', methods=['POST'])
def process_payment():
    try:
        data = request.json
        
        # Create a payment method
        payment_method = circle.payments.create_card(
            idempotencyKey=os.urandom(8).hex(),
            keyId="key1",
            encryptedData={
                "number": data['cardNumber'],
                "cvv": data['cvv']
            },
            billingDetails={
                "name": "Test User",
                "city": "Test City",
                "country": "US",
                "line1": "Test Address",
                "postalCode": "12345"
            },
            expMonth=int(data['expMonth']),
            expYear=int(data['expYear'])
        )

        # Create a payment using the payment method
        payment = circle.payments.create_payment(
            idempotencyKey=os.urandom(8).hex(),
            amount={
                "amount": str(float(data['amount'])),
                "currency": "USD"
            },
            source={
                "id": payment_method['id'],
                "type": "card"
            },
            description="Test payment"
        )

        return jsonify({
            "success": True,
            "message": f"Payment processed successfully! Payment ID: {payment['id']}"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error processing payment: {str(e)}"
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
