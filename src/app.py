from flask import Flask, request, jsonify, render_template
from handlers.auth import is_authorized
from handlers.calculations import calculate_totals
from handlers.expenditures import post_expenditure, get_expenditures

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    totals = calculate_totals()
    return render_template('dashboard.html', totals=totals)

@app.route('/expenditures', methods=['POST'])
def expenditures():
    if not is_authorized(request):
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    amount = data.get('amount')
    description = data.get('description')
    date = data.get('date')
    
    if post_expenditure(amount, description, date):
        return jsonify({"message": "Expenditure posted successfully"}), 201
    else:
        return jsonify({"error": "Failed to post expenditure"}), 400

@app.route('/expenditures', methods=['GET'])
def expenditures_list():
    expenditures = get_expenditures()
    return jsonify(expenditures)

if __name__ == '__main__':
    app.run(debug=True)