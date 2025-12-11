// script.js (Add these functions near the top, before the main event listener)

// --- GLOBAL ELEMENT REFERENCES (Moved out of DOMContentLoaded to fix ReferenceError) ---
// These elements must be defined here so the rendering functions can access them directly.
const playerListContainer = document.getElementById('player-recommendation-list');
const playerListHeader = document.getElementById('player-list-header');
const resultsContainer = document.getElementById('results-container'); // The detailed box showing stats/score
const recommendationsSection = document.getElementById('recommendations-section'); // The container for all results

// Helper function to create the HTML string for a single player card
function createPlayerCardHTML(playerData) {
    // Determine the color for the score based on the score value
    let scoreColor = 'text-red-500';
    if (playerData.reco_score >= 75) {
        scoreColor = 'text-green-500';
    } else if (playerData.reco_score >= 45) {
        scoreColor = 'text-yellow-400';
    }

    return `
        <div class="bg-gray-700 p-6 rounded-xl shadow-lg border-l-4 border-yellow-600 hover:shadow-xl hover:shadow-yellow-500/10 transition duration-300">
            <h4 class="font-header text-2xl font-extrabold text-white mb-2">${playerData.player_name || 'N/A'}</h4>
            <p class="text-md text-gray-400 mb-3">
                ${playerData.position || 'N/A'} - ${playerData.team || 'N/A'}
            </p>
            <p class="text-xl text-gray-300">
                Score:
                <span class="font-extrabold ${scoreColor}">
                    ${playerData.reco_score ? playerData.reco_score.toFixed(2) : '--'}%
                </span>
            </p>
            <p class="text-sm text-gray-400 mt-1">${playerData.reco_conclusion}</p>
        </div>
    `;
}

// Function to render a list of players (for team lookups)
function renderPlayerList(dataArray) {
    playerListContainer.innerHTML = '';

    // Set the header to show the team that was searched
    const teamName = dataArray.length > 0 ? dataArray[0].team : 'Team';
    // Ensure dataArray[0].input_week exists before accessing it
    const weekDisplay = dataArray.length > 0 && dataArray[0].input_week ? dataArray[0].input_week : 'N/A';
    playerListHeader.textContent = `Top Fantasy Options for the ${teamName} (Week ${weekDisplay})`;

    // Sort the players by score (highest first) for the best recommendation order
    dataArray.sort((a, b) => b.reco_score - a.reco_score);

    if (dataArray.length > 0) {
        dataArray.forEach(player => {
            playerListContainer.insertAdjacentHTML('beforeend', createPlayerCardHTML(player));
        });
    } else {
         playerListContainer.innerHTML = '<p class="text-lg text-gray-400 text-center p-4">No skill position data found for that team this week.</p>';
    }

    // Hide the detailed single-player view when showing a list
    resultsContainer.style.display = 'none';
    recommendationsSection.classList.remove('hidden');
}

// Function to render a single player (refactoring your existing logic)
function renderSinglePlayerDetail(data) {
    // Hide the list container when showing a single detailed view
    playerListContainer.innerHTML = '';
    playerListHeader.textContent = "Detailed Player Analysis"; // Update the header

    // Define linguistic conclusion and class (your existing logic)
    let conclusionText;
    let conclusionClass;
    let score = data.reco_score;

    if (score >= 75) {
        conclusionText = "🔥 MUST START (Elite Potential)";
        conclusionClass = "text-green-400 bg-green-900/50";
    } else if (score >= 45) {
        conclusionText = "🟢 FLEX / HIGH POTENTIAL START (Solid Play)";
        conclusionClass = "text-yellow-400 bg-yellow-900/50";
    } else {
        conclusionText = "🔴 SIT / LOW FLEX (Risky Play)";
        conclusionClass = "text-red-400 bg-red-900/50";
    }

    // DOM MANIPULATION (Injecting data into the detailed results container)
    const conclusionElement = document.getElementById('conclusion');
    conclusionElement.textContent = conclusionText;
    conclusionElement.className = `font-body text-xl font-bold p-2 rounded-md ${conclusionClass}`;

    document.getElementById('player-name-display').textContent = `${data.player_name} (${data.team} - ${data.position})`;
    document.getElementById('recommendation-score').textContent = `${score.toFixed(2)} /100`;

    // Input Stats
    document.getElementById('input-year').textContent = data.input_year;
    document.getElementById('input-week').textContent = data.input_week;
    document.getElementById('stat-volume').textContent = data.volume;
    document.getElementById('stat-yards').textContent = data.yards;
    document.getElementById('stat-receptions').textContent = data.receptions;
    document.getElementById('stat-td').textContent = data.td;

    // Display the results
    resultsContainer.style.display = 'block';
    recommendationsSection.classList.remove('hidden');
}


// This event listener ensures the script runs only after the entire HTML document is loaded.
document.addEventListener('DOMContentLoaded', () => {

    // --- Element References ---
    const playerInput = document.getElementById('player-input'); // The text field for the player/team name
    const form = document.getElementById('preferences-form'); // The main submission form
    const weekInput = document.getElementById('week-input'); // Reference for the Week input
    const yearInput = document.getElementById('year-input'); // <<< NEW: Reference for the Year input

    // References for the submission button state
    const submitButton = document.getElementById('submit-button');
    const buttonText = document.getElementById('button-text');
    const spinner = document.getElementById('spinner');

    // References for the output display areas
    const errorMessage = document.getElementById('error-message');


    // Handle Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // 1. Setup UI for loading state
        submitButton.disabled = true;
        buttonText.textContent = 'Analyzing...';
        spinner.classList.remove('hidden');

        // Hide previous results and errors
        recommendationsSection.classList.add('hidden');
        resultsContainer.style.display = 'none';
        errorMessage.textContent = '';

        // --- NEW LOGIC: Extract Year and Week from separate inputs ---
        const playerOrTeam = playerInput.value.trim();
        const weekValue = weekInput.value.trim(); // Read week directly
        const yearValue = yearInput.value.trim(); // <<< NEW: Read year directly

        if (!playerOrTeam || !weekValue || !yearValue) {
            // Restore button state and alert the user if fields are empty.
            submitButton.disabled = false;
            buttonText.textContent = 'Analyze Player/Team';
            spinner.classList.add('hidden');
            alert("Please enter a player name/team, week, and year.");
            return;
        }

        // Prepare the data payload to send to the Flask backend.
        const userInputs = {
            player_or_team_input: playerOrTeam,
            year: yearValue,               // Send year as a string
            week: weekValue                // Send week as a string
        };

        try {
            // 2. Fetch data from Flask endpoint
            // The fetch() request targets the '/analyze_player' route defined in app.py.
            const response = await fetch('/analyze_player', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userInputs) // Payload now includes player, year, and week
            });

            // Check if the HTTP response status code indicates success (200-299 range).
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({error: response.statusText}));
                throw new Error(`${errorData.error || response.statusText}`);
            }

            // 3. Process successful JSON data
            const data = await response.json();

            // --- NEW DEBUGGING LOGS ---
            console.log('--- ANALYSIS RESULTS ---');
            console.log('Received data:', data);
            console.log('Is Array:', Array.isArray(data));
            console.log('Array Length:', data.length);
            // --------------------------

            // 4. Determine rendering based on array content
            if (Array.isArray(data) && data.length === 1) {
                // It's a single player (we take the first item in the array)
                if (data[0]) {
                    renderSinglePlayerDetail(data[0]);
                } else {
                    errorMessage.textContent = 'Error: Single player data was null.';
                    recommendationsSection.classList.remove('hidden');
                }

            } else if (Array.isArray(data) && data.length > 1) {
                // It's a team search (returns a list of multiple players)
                renderPlayerList(data);

            } else if (Array.isArray(data) && data.length === 0) {
                // It's an empty result (no player or team found)
                errorMessage.textContent = 'No player or team data found for your search in the selected week/year.';
                recommendationsSection.classList.remove('hidden');

            } else {
                // Fallback error for unexpected data structure
                errorMessage.textContent = 'Unexpected error: Received data is not a recognized list format.';
                recommendationsSection.classList.remove('hidden');
            }

        // Scroll to results
        window.scrollTo({
            top: recommendationsSection.offsetTop - 50,
            behavior: 'smooth'
        });

    } catch (error) {
            // 6. Handle any fetch or processing errors
            console.error('Error fetching analysis:', error);
            errorMessage.textContent = error.message;
            recommendationsSection.classList.remove('hidden');
        } finally {
            // 7. Restore button state regardless of success or failure
            submitButton.disabled = false;
            buttonText.textContent = 'Analyze Player/Team';
            spinner.classList.add('hidden');
        }
    });

}); // End of DOMContentLoaded