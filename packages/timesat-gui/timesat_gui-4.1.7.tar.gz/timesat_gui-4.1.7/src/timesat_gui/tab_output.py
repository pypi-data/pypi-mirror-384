from flask import Blueprint, session, request, jsonify
import json

tab_output_bp = Blueprint('tab_output', __name__)


# 更新变量并生成曲线图
@tab_output_bp.route("/update_other", methods=["POST"])
def update_other():
    try:
        # Retrieve the data sent from the frontend
        data = request.get_json()

        # Ensure data is received properly
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Track updates and missing keys
        updated_keys = []
        missing_keys = []

        # Update session parameters based on user input
        for key, value in data.items():
            if key in session:
                # Update session with new value
                session[key] = value
                updated_keys.append(key)
            else:
                # Track keys that don't exist in session
                missing_keys.append(key)
                print(f"Warning: {key} is not found in session.")

        # Create a response summarizing the updates
        response = {
            "updated_keys": updated_keys,
            "missing_keys": missing_keys,
            "message": "Session updated successfully" if updated_keys else "No keys updated"
        }

        # Return the JSON response
        return jsonify(response), 200

    except Exception as e:
        # Handle any unexpected errors and return an error response
        return jsonify({"error": str(e)}), 500

