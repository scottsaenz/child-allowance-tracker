from flask import Flask, jsonify, render_template, request

from handlers.auth import is_authorized
from handlers.calculations import calculate_totals
from handlers.expenditures import get_expenditures, post_expenditure
from utils.logger import get_logger

# Set up logging
logger = get_logger(__name__)

# Configure Flask to look for templates in src/templates
app = Flask(__name__, template_folder="templates", static_folder="static")


@app.route("/")
def index():
    logger.info("Index page requested")
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    logger.info("Dashboard page requested")
    totals = calculate_totals()
    return render_template("dashboard.html", totals=totals)


@app.route("/expenditures", methods=["POST"])
def expenditures():
    logger.info("POST expenditure request received")

    if not is_authorized(request):
        logger.warning("Unauthorized expenditure request")
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    child_name = data.get("child_name")
    amount = data.get("amount")
    description = data.get("description")
    date = data.get("date")

    logger.info(f"Processing expenditure: {child_name}, ${amount}")

    if post_expenditure(child_name, amount, date, description):
        logger.info("Expenditure posted successfully")
        return jsonify({"message": "Expenditure posted successfully"}), 201
    else:
        logger.error("Failed to post expenditure")
        return jsonify({"error": "Failed to post expenditure"}), 400


@app.route("/expenditures", methods=["GET"])
def expenditures_list():
    logger.info("GET expenditures request received")
    expenditures = get_expenditures()
    return jsonify(expenditures)


if __name__ == "__main__":
    logger.info("Starting Flask application")
    app.run(debug=False)
