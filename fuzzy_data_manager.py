import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import nfl_data_py as nfl #need python 3.12 or lower
import pandas as pd
from typing import Dict, Any

# --- 1. FUZZY LOGIC SETUP ---
# Inputs: Player statistics that influence the decision (Antecedents)
# Fantasy football metrics are usually continuous and highly subjective in classification (Low/Medium/High).

# Carries/Targets (Volume): The combined number of rush attempts (RB) and targets (WR/RB)
# High volume is generally a strong predictor. Range is set from 0 to 30.
volume = ctrl.Antecedent(np.arange(0, 31, 1), 'volume')

# Yards (Efficiency/Production): Total scrimmage yards (Rushing + Receiving)
# Yards are the base of fantasy scoring. Range is set from 0 to 150.
yards = ctrl.Antecedent(np.arange(0, 151, 1), 'yards')

# Receptions (PPR Value): The number of receptions (crucial for PPR leagues)
# Measures involvement in the passing game. Range is set from 0 to 15.
receptions = ctrl.Antecedent(np.arange(0, 16, 1), 'receptions')

# Touchdowns (TD): The most volatile but highest-value metric.
# Range is set from 0 to 3.
td = ctrl.Antecedent(np.arange(0, 4, 1), 'td')

# Output: The final recommendation score (Consequent)
# The final crisp score will be between 0 (Hard Sit) and 100 (Must Start)
recommendation = ctrl.Consequent(np.arange(0, 101, 1), 'recommendation')

# --- 1.2 Define Membership Functions (MFs) ---
# Using Triangular MFs for simplicity, interpretability, and low computational cost,
# as justified by the literature (e.g., COMET/FTOPSIS methods).

# --- 1.3 Fuzzy Sets: Low, Medium, High for inputs, and Sit, Flex, Start for the output ---

# Volume (0-30 carries/targets)
volume['low'] = fuzz.trimf(volume.universe, [0, 0, 8])
volume['medium'] = fuzz.trimf(volume.universe, [3, 13, 22])
volume['high'] = fuzz.trimf(volume.universe, [18, 30, 30]) #Tightens overlap between medium and high to be more decisive

# Yards (0-150 yards)
yards['poor'] = fuzz.trimf(yards.universe, [0, 0, 45])
yards['average'] = fuzz.trimf(yards.universe, [20, 70, 110])
yards['elite'] = fuzz.trimf(yards.universe, [100, 130, 150]) #Makes achieving elite harder to better reflect difficulty of hitting 100+ yards

# Receptions (0-15 receptions)
receptions['low'] = fuzz.trimf(receptions.universe, [0, 0, 4])
receptions['decent'] = fuzz.trimf(receptions.universe, [2, 7, 12])
receptions['high'] = fuzz.trimf(receptions.universe, [10, 15, 15])

# Touchdowns (0-3 TD)
td['none'] = fuzz.trimf(td.universe, [0, 0, 0.5])
td['one'] = fuzz.trimf(td.universe, [0, 1, 2])
td['multiple'] = fuzz.trimf(td.universe, [1, 3, 3])


# Recommendation Output (0-100 score)
recommendation['sit'] = fuzz.trimf(recommendation.universe, [0, 0, 40])
recommendation['flex'] = fuzz.trimf(recommendation.universe, [20, 50, 80])
recommendation['start'] = fuzz.trimf(recommendation.universe, [60, 100, 100])

# --- 1.4 Define Fuzzy Rules (Rule Base) ---
# A simplified set of 12 rules (out of 3^4 = 81 potential rules) focusing on common scenarios.
# The use of the Mamdani MIN-MAX method for aggregation ensures high interpretability.

rule1 = ctrl.Rule(
    (volume['high'] | receptions['high']) & yards['elite'] & td['multiple'],
    recommendation['start']
)
# Justification: Elite volume/receptions with elite yards AND multiple TDs = Must Start.

rule2 = ctrl.Rule(
    (volume['low'] & receptions['low']) | yards['poor'] & td['none'],
    recommendation['sit']
)
# Justification: Low volume, low efficiency, no TDs = Hard Sit.

rule3 = ctrl.Rule(
    volume['medium'] & yards['average'] & receptions['decent'] & td['one'],
    recommendation['start']
)
# Justification: Solid all-around performance with a TD = Safe Start.

rule4 = ctrl.Rule(
    (volume['medium'] | receptions['decent']) & yards['average'] & td['none'],
    recommendation['flex']
)
# Justification: Decent floor, but lacking the high ceiling of a TD = Flex consideration.

rule5 = ctrl.Rule(
    volume['low'] & yards['poor'] & receptions['low'],
    recommendation['sit']
)
# Justification: Low production across the board means high risk.

rule6 = ctrl.Rule(
    volume['high'] & yards['poor'] & td['none'],
    recommendation['sit']
)
# Justification: High volume but zero efficiency/score = Inefficient, Sit.

rule7 = ctrl.Rule(
    yards['elite'] & td['multiple'],
    recommendation['start']
)
# Justification: Exceptional efficiency and TDs overpowers moderate volume.

rule8 = ctrl.Rule(
    td['multiple'] & (volume['medium'] | yards['average']),
    recommendation['start']
)
# Justification: Multiple TDs is a high leverage event, justifying a start.

rule9 = ctrl.Rule(
    volume['medium'] & yards['average'] & td['none'],
    recommendation['flex']
)
# Justification: Mediocre floor, no ceiling.

rule10 = ctrl.Rule(
    (volume['high'] | receptions['high']) & yards['average'] & td['none'],
    recommendation['flex']
)
# Justification: Good volume floor, but needs the TD/Elite Yards for a definite start.

rule11 = ctrl.Rule(
    receptions['high'] & yards['elite'],
    recommendation['start']
)
# Justification: Strong PPR floor combined with elite yards is a must-start.

rule12 = ctrl.Rule(
    volume['medium'] & yards['poor'] & receptions['low'],
    recommendation['sit']
)
# Justification: Clear lack of production despite getting some touches.


# Rule 13: The High-Volume, Zero-Efficiency BUST (Hard SIT)
# Justification: Getting lots of touches (high volume) but zero yards, zero TDs, and zero receptions means the usage is completely ineffective.
rule13 = ctrl.Rule(
    volume['high'] & yards['poor'] & receptions['low'] & td['none'],
    recommendation['sit']
)

# Rule 14: The Ultra-Efficient, Low-Volume Ceiling (START)
# Justification: Even with low volume, achieving elite yards and multiple TDs is a highly successful fantasy outcome that must result in a START recommendation.
rule14 = ctrl.Rule(
    volume['low'] & yards['elite'] & td['multiple'],
    recommendation['start']
)

# Rule 15: The PPR Safety Net (High FLEX)
# Justification: Low volume and average yards are normally a FLEX, but high receptions establishes a strong PPR floor, justifying a higher score.
rule15 = ctrl.Rule(
    volume['low'] & receptions['high'] & yards['average'] & td['none'],
    recommendation['flex']
)

# Rule 16: The Decent Floor, No Ceiling (Medium FLEX)
# Justification: Average production across the board (medium volume, decent receptions, average yards) but no TD often represents the definition of a safe, standard FLEX play.
rule16 = ctrl.Rule(
    volume['medium'] & receptions['decent'] & yards['average'] & td['none'],
    recommendation['flex']
)

# Rule 17: The TD-Dependent Fluke (SIT/LOW FLEX)
# Justification: A single TD can mask a lack of underlying production (low volume, poor yards). Score should be pulled down to a risky FLEX or SIT.
rule17 = ctrl.Rule(
    volume['low'] & yards['poor'] & receptions['low'] & td['one'],
    recommendation['sit']
)

# Rule 18: The Workhorse Floor with TD Ceiling (Safe START)
# Justification: High volume combined with average yards and the crucial TD makes for a highly reliable fantasy START.
rule18 = ctrl.Rule(
    volume['high'] & yards['average'] & td['one'],
    recommendation['start']
)

# Rule 19: The Pure Efficiency Floor (High FLEX)
# Justification: Elite yards without the TD ceiling, combined with good volume, is a very strong FLEX play, but not an unquestionable START.
rule19 = ctrl.Rule(
    volume['medium'] & yards['elite'] & td['none'],
    recommendation['flex']
)

# --- 1.5 Create the Control System and Simulation ---
# Assemble the rules into a Control System
manager_ctrl = ctrl.ControlSystem([
    rule1, rule2, rule3, rule4, rule5, rule6,
    rule7, rule8, rule9, rule10, rule11, rule12,
    rule13, rule14, rule15, rule16, rule17, rule18, rule19,
])

# Create the Simulation/Decision Engine
manager_sim = ctrl.ControlSystemSimulation(manager_ctrl)

# --- 2. DATA RETRIEVAL FUNCTION ---
# Dictionary mapping common team names/nicknames to their 3-letter abbreviations
# This makes the user input more flexible (e.g., 'Eagles' or 'PHI')
TEAM_ABBREVIATIONS = {
    # --- Official Team Names (Key: Lowercase Name, Value: Abbreviation) ---
    '49ers': 'SF', 'bears': 'CHI', 'bengals': 'CIN', 'bills': 'BUF', 'broncos': 'DEN',
    'browns': 'CLE', 'buccaneers': 'TB', 'cardinals': 'ARI', 'chargers': 'LAC',
    'chiefs': 'KC', 'colts': 'IND', 'cowboys': 'DAL', 'dolphins': 'MIA',
    'eagles': 'PHI', 'falcons': 'ATL', 'giants': 'NYG', 'jaguars': 'JAX',
    'jets': 'NYJ', 'lions': 'DET', 'packers': 'GB', 'panthers': 'CAR',
    'patriots': 'NE', 'raiders': 'LV', 'rams': 'LAR', 'ram': 'LAR', 'ravens': 'BAL',
    'saints': 'NO', 'seahawks': 'SEA', 'steelers': 'PIT', 'texans': 'HOU',
    'titans': 'TEN', 'vikings': 'MIN', 'washington commanders': 'WAS',
    'commanders': 'WAS',  # Common shortened name for Washington
    'racers': 'LAR',  # Common error fix (Rams are LAR, not Racers)

    # --- Official Abbreviated Lookups (Key: Abbreviation in lowercase, Value: Abbreviation) ---
    # AFC East
    'buf': 'BUF', 'ne': 'NE', 'mia': 'MIA', 'nyj': 'NYJ',
    # AFC North
    'bal': 'BAL', 'cin': 'CIN', 'cle': 'CLE', 'pit': 'PIT',
    # AFC South
    'hou': 'HOU', 'ind': 'IND', 'jax': 'JAX', 'ten': 'TEN',
    # AFC West
    'den': 'DEN', 'kc': 'KC', 'lac': 'LAC', 'lv': 'LV',
    # NFC East
    'dal': 'DAL', 'nyg': 'NYG', 'phi': 'PHI', 'was': 'WAS',
    # NFC North
    'chi': 'CHI', 'det': 'DET', 'gb': 'GB', 'min': 'MIN',
    # NFC South
    'atl': 'ATL', 'car': 'CAR', 'no': 'NO', 'tb': 'TB',
    # NFC West
    'ari': 'ARI', 'lar': 'LAR', 'sf': 'SF', 'sea': 'SEA',
}


def get_weekly_team_stats(team_input: str, year: int, week: int) -> list[Dict[str, Any]]:
    """
    Fetches raw NFL stats for all relevant fantasy players on a specific team
    for a given year and week.
    """
    print(f"Fetching weekly data for Team: {team_input} ({year} Week {week})...")

    # Standardize the input to a consistent 2-letter abbreviation
    standardized_team = TEAM_ABBREVIATIONS.get(team_input.lower(), team_input.upper())

    # 1. Define Columns and Import Data (using the same columns as before)
    cols_to_pull = [
        'player_display_name', 'recent_team', 'position', 'week', 'carries', 'rushing_yards',
        'rushing_tds', 'receptions', 'targets', 'receiving_yards', 'receiving_tds'
    ]

    try:
        df = nfl.import_weekly_data([year], columns=cols_to_pull)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

    # 2. Filter by Team and Week
    team_data = df[
        (df['recent_team'] == standardized_team) &  # Filter by the standardized team abbreviation
        (df['week'] == week)
        ]

    if team_data.empty:
        print(f"Team '{team_input}' not found or no data for Week {week}.")
        return []

    # 3. Filter by Relevant Fantasy Positions (RB, WR, TE)
    # Exclude QBs, K, and DEF because the fuzzy system is not designed for them.
    relevant_positions = ['RB', 'WR', 'TE']
    fantasy_team_stats = team_data[team_data['position'].isin(relevant_positions)]

    # 4. Process and Calculate Fuzzy Inputs for Each Player
    results_list = []

    for index, player_stats in fantasy_team_stats.iterrows():
        # Calculate the four fuzzy inputs, just like in the single player function
        volume_calc = player_stats.get('carries', 0) + player_stats.get('targets', 0)
        yards_calc = player_stats.get('rushing_yards', 0) + player_stats.get('receiving_yards', 0)
        receptions_calc = player_stats.get('receptions', 0)
        td_calc = player_stats.get('rushing_tds', 0) + player_stats.get('receiving_tds', 0)

        # Store the raw inputs along with player info
        player_result = {
            'name': player_stats.get('player_display_name'),
            'team': player_stats.get('recent_team'),
            'position': player_stats.get('position'),
            'volume': int(volume_calc),
            'yards': int(yards_calc),
            'receptions': int(receptions_calc),
            'td': int(td_calc),
        }
        results_list.append(player_result)

    return results_list
def get_seasonal_player_stats(player_name: str, year: int, week: int) ->Dict[str, Any]:
    # Define the columns we need for calculation:
    # player_display_name is used for filtering
    # rush_attempt, receptions, receiving_yards, rushing_yards, receiving_td, rushing_td
    cols_to_pull = [
        'player_display_name', 'recent_team', 'position', 'week', 'carries', 'rushing_yards',
        'rushing_tds', 'receptions', 'targets', 'receiving_yards', 'receiving_tds'
    ]

    # 1. Import Seasonal Data
    try:
        df = nfl.import_seasonal_data([year], 'REG')

        player_id_df = df[df['player_display_name'] == player_name]
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {}

    # 2. Filter by Player Name and Week
    player_data = df[
        (df['player_display_name'].str.contains(player_name, case=False, na=False)) &
        (df['week'] == week)
        ]

    if player_data.empty:
        print(f"Player '{player_name}' not found for Week {week} or data is missing.")
        return {}

    # Take the first match if multiple exist (which shouldn't happen with display name)
    player_stats = player_data.iloc[0]

    # 3. Calculate Fuzzy Inputs

    # 'volume' = Carries + Targets
    volume_calc = player_stats.get('carries', 0) + player_stats.get('targets', 0)

    # 'yards' = Rushing Yards + Receiving Yards
    yards_calc = player_stats.get('rushing_yards', 0) + player_stats.get('receiving_yards', 0)

    # 'receptions' = Receptions
    receptions_calc = player_stats.get('receptions', 0)

    # 'td' = Rushing TDs + Receiving TDs
    td_calc = player_stats.get('rushing_tds', 0) + player_stats.get('receiving_tds', 0)

    # 4. Return as a dictionary
    return {
        'name': player_stats.get('player_display_name'),
        'team': player_stats.get('recent_team'),
        'position': player_stats.get('position'),
        'volume': int(volume_calc),
        'yards': int(yards_calc),
        'receptions': int(receptions_calc),
        'td': int(td_calc),
    }

def get_weekly_player_stats(player_name: str, year: int, week: int) ->Dict[str, Any]:
    """
    Fetches raw NFL stats for a specific player, year, and week, then calculates
    the 4 required fuzzy inputs.
    :param player_name:
    :param year:
    :param week:
    :return:
    """
    print(f"Fetching weekly data for {year} Week {week}...")

    # Define the columns we need for calculation:
    # player_display_name is used for filtering
    # rush_attempt, receptions, receiving_yards, rushing_yards, receiving_td, rushing_td
    cols_to_pull = [
        'player_display_name', 'recent_team', 'position', 'week', 'carries', 'rushing_yards',
        'rushing_tds', 'receptions', 'targets', 'receiving_yards', 'receiving_tds'
    ]

    # 1. Import Weekly Data
    # NOTE: This pulls the whole season's data and can take a moment.
    try:
        df = nfl.import_weekly_data([year], columns=cols_to_pull)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {}

    # 2. Filter by Player Name and Week
    player_data = df[
        (df['player_display_name'].str.contains(player_name, case=False, na=False)) &
        (df['week'] == week)
        ]

    if player_data.empty:
        print(f"Player '{player_name}' not found for Week {week} or data is missing.")
        return {}

    # Take the first match if multiple exist (which shouldn't happen with display name)
    player_stats = player_data.iloc[0]

    # 3. Calculate Fuzzy Inputs

    # 'volume' = Carries + Targets
    volume_calc = player_stats.get('carries', 0) + player_stats.get('targets', 0)

    # 'yards' = Rushing Yards + Receiving Yards
    yards_calc = player_stats.get('rushing_yards', 0) + player_stats.get('receiving_yards', 0)

    # 'receptions' = Receptions
    receptions_calc = player_stats.get('receptions', 0)

    # 'td' = Rushing TDs + Receiving TDs
    td_calc = player_stats.get('rushing_tds', 0) + player_stats.get('receiving_tds', 0)

    # 4. Return as a dictionary
    return {
        'name': player_stats.get('player_display_name'),
        'team': player_stats.get('recent_team'),
        'position': player_stats.get('position'),
        'volume': int(volume_calc),
        'yards': int(yards_calc),
        'receptions': int(receptions_calc),
        'td': int(td_calc),
    }

def is_team_input(text: str) -> bool:
    """Checks if the input string is likely a team name or abbreviation."""
    text_lower = text.lower()
    return text_lower in TEAM_ABBREVIATIONS or text.upper() in TEAM_ABBREVIATIONS.values()

# --- 3. EXECUTION AND INTEGRATION FUNCTION ---
def run_fuzzy_analysis(player_name_or_team: str, year: int, week: int):
    """
    Main function to fetch data and run the fuzzy simulation
    :param player_name_or_team:
    :param year:
    :param week:
    :return:
    """
    # 1. Determine Input Type and Get Raw Stats
    if is_team_input(player_name_or_team):
        # Input is a team name (e.g., 'Chiefs'). Get stats for all fantasy players on that team.
        raw_stats_list = get_weekly_team_stats(player_name_or_team, year, week)
    else:
        # Input is a player name. Get stats for only that player.
        # We wrap the single player's dictionary result in a list for consistency.
        single_stat_dict = get_weekly_player_stats(player_name_or_team, year, week)
        raw_stats_list = [single_stat_dict] if single_stat_dict else []

    if not raw_stats_list:
        return f"Analysis failed: Could not retrieve stats for {player_name_or_team}."

    final_results = []

    # 2. Iterate through all players retrieved and run the Fuzzy Simulation
    for stats in raw_stats_list:

        # NOTE: Skip if a player's stats dictionary is empty (e.g., if a player was found but had 0 stats)
        if not stats:
            continue

        # Clamp values to the defined Universe of Discourse
        volume_input = min(max(stats['volume'], 0), 30)
        yards_input = min(max(stats['yards'], 0), 150)
        receptions_input = min(max(stats['receptions'], 0), 15)
        td_input = min(max(stats['td'], 0), 3)

        # @@@DEBUG Statements remove later
        # print(f"\n--- Crisp Inputs for {stats['name']} (Week {week}) ---")
        # print(f"Volume: {volume_input} (Carries+Targets)")

        try:
            manager_sim.input['volume'] = volume_input
            manager_sim.input['yards'] = yards_input
            manager_sim.input['receptions'] = receptions_input
            manager_sim.input['td'] = td_input

            manager_sim.compute()

            reco_score = manager_sim.output['recommendation']
            reco_conclusion = convert_score_to_recommendation(reco_score)

            # 3. Compile the Final Result Dictionary
            player_result = {
                "player_name": stats['name'],
                "team": stats['team'],
                "position": stats['position'],
                "volume": stats['volume'],
                "yards": stats['yards'],
                "receptions": stats['receptions'],
                "td": stats['td'],
                "reco_score": reco_score,
                "reco_conclusion": reco_conclusion,
                "input_year": year,
                "input_week": week
            }
            final_results.append(player_result)

        except ValueError as e:
            print(f"\nError running fuzzy system for {stats['name']}: {e}")
            # If fuzzy computation fails for one player, just log it and move to the next.
            continue

    # If the input was a player name, return the single result.
    # If it was a team, return the list of results.
    return final_results


def convert_score_to_recommendation(score):
    """Converts the crisp score into a linguistic recommendation."""
    if score >= 75:
        return "🔥 MUST START"
    elif score >= 45:
        return "🟢 FLEX / HIGH POTENTIAL START"
    else:
        return "🔴 SIT / LOW FLEX"

# # --- 4. EXAMPLE USAGE ---
#
# # Find current year and week to make the data relevant
# CURRENT_YEAR = 2024 # Adjust this to the current NFL season year
# CURRENT_WEEK = 12   # Adjust this to the most recent completed week
#
# # Example 1: A top-tier player (e.g., Christian McCaffrey)
# run_fuzzy_analysis("Christian McCaffrey", CURRENT_YEAR, CURRENT_WEEK)
#
# # Example 2: A bench player or one with a bad week
# # run_fuzzy_analysis("Ezekiel Elliott", CURRENT_YEAR, CURRENT_WEEK)