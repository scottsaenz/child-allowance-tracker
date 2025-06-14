from flask import Blueprint, request, jsonify
from services.google_sheets import append_expenditure, get_expenditures
from handlers.auth import is_user_authorized
from models.expenditure import Expenditure

expenditures_bp = Blueprint('expenditures', __name__)

@expenditures_bp.route('/expenditures', methods=['POST'])
def post_expenditure():
    if not is_user_authorized(request.json.get('user_id')):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    try:
        expenditure = Expenditure(
            amount=data['amount'],
            date=data['date'],
            description=data['description']
        )
        append_expenditure(expenditure)
        return jsonify({"message": "Expenditure added successfully"}), 201
    except KeyError as e:
        return jsonify({"error": f"Missing field: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@expenditures_bp.route('/expenditures', methods=['GET'])
def get_all_expenditures():
    expenditures = get_expenditures()
    return jsonify(expenditures), 200