from flask import Flask, render_template, request, jsonify, render_template_string
from fuzzy_data_manager import run_fuzzy_analysis # import fuzzy logic execution function

# 1. Flask Setup: Initializes the web application
app = Flask(__name__)

# --- Configuration (Hard set the current NFL season details) ---
CURRENT_YEAR = 2025
CURRENT_WEEK = 15


# Route to handle the AJAX POST request from the HTML form
@app.route('/analyze_player', methods=['POST'])
def analyze_player():
    # 2. Get the JSON data sent from the JavaScript fetch request
    data = request.get_json()
    player_input = data.get('player_or_team_input')
    selected_year = data.get('year')
    selected_week = data.get('week')

    try:
        year = int(selected_year)
        week = int(selected_week)
    except (ValueError, TypeError):
        # Handle cases where year/week might be missing or invalid
        return jsonify({"error": "Invalid year or week selected."}), 400

    if not player_input:
        return jsonify({'error': 'No player name provided.'}), 400

    try:
        # 2. Call the Fuzzy Logic Function
        result_data = run_fuzzy_analysis(player_input, year, week)

        # 3. Handle case where run_fuzzy_analysis couldn't find data
        if isinstance(result_data, str) and "Analysis failed" in result_data:
            return jsonify({'error': result_data}), 404

        # 4. Return the analysis result as JSON back to the JavaScript
        # Example JSON response
        # {
        #     "player_name": "Christian McCaffrey",
        #     "team": "SF",
        #     "position": "RB",
        #     "volume": 25,
        #     "yards": 130,
        #     "receptions": 8,
        #     "td": 2,
        #     "reco_score": 98.75,
        #     "input_year": 2024,
        #     "input_week": 12
        # }
        return jsonify(result_data)


    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({'error': 'An internal server error occurred during analysis.'}), 500

# --- Basic Route to serve the HTML/JS frontend ---
@app.route('/')
def index():
    """Renders the HTML file directly for the frontend."""
    return render_template_string(open('index.html').read())

if __name__ == '__main__':
    app.run(debug=True)