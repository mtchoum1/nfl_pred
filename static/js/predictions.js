const yearSelect = document.getElementById('year-select');
const seasontypeSelect = document.getElementById('seasontype-select');
const weekSelect = document.getElementById('week-select');
const scheduleGrid = document.getElementById('schedule-grid');
const loader = document.getElementById('loader');
const errorMessage = document.getElementById('error-message');
const errorText = document.getElementById('error-text');
const accuracySummary = document.getElementById('accuracy-summary');

function populateSelectors() {
    const currentYear = new Date().getFullYear();
    for (let year = currentYear + 1; year >= 2022; year--) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        if (year === currentYear) option.selected = true;
        yearSelect.appendChild(option);
    }
    updateWeekSelector();
}

function updateWeekSelector() {
    weekSelect.innerHTML = '';
    const seasonType = seasontypeSelect.value;
    const weeks = (seasonType == '2') ? 18 : 5;
    const weekName = (seasonType == '2') ? 'Week' : 'Playoff Week';

    for (let week = 1; week <= weeks; week++) {
        const option = document.createElement('option');
        option.value = week;
        option.textContent = `${weekName} ${week}`;
        weekSelect.appendChild(option);
    }
}

async function fetchPredictions() {
    const year = yearSelect.value;
    const seasontype = seasontypeSelect.value;
    const week = weekSelect.value;
    
    loader.classList.remove('hidden');
    scheduleGrid.innerHTML = '';
    errorMessage.classList.add('hidden');
    accuracySummary.classList.add('hidden');

    try {
        const response = await fetch(`/api/predict/${year}/${seasontype}/${week}`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        displayGames(data.games);
        displayAccuracy(data.accuracy);
    } catch (error) {
        console.error('Fetch error:', error);
        errorText.textContent = error.message;
        errorMessage.classList.remove('hidden');
    } finally {
        loader.classList.add('hidden');
    }
}

function displayAccuracy(accuracy) {
    if (accuracy && accuracy.total > 0) {
        document.getElementById('correct-count').textContent = accuracy.correct;
        document.getElementById('total-count').textContent = accuracy.total;
        document.getElementById('percentage').textContent = accuracy.percentage.toFixed(2);
        accuracySummary.classList.remove('hidden');
    }
}

function displayGames(games) {
    if (!games || games.length === 0) {
         scheduleGrid.innerHTML = `<div class="col-span-full text-center bg-white rounded-lg shadow p-8">
                                      <h3 class="text-xl font-semibold text-gray-700">No Games Found</h3>
                                      <p class="text-gray-500 mt-2">The schedule for this week may not be available yet.</p>
                                   </div>`;
         return;
    }
    
    games.forEach(game => {
        const gameCard = document.createElement('div');
        let predictionBorderClass = 'pending-prediction';
        if (game.is_correct === true) predictionBorderClass = 'correct-prediction';
        else if (game.is_correct === false) predictionBorderClass = 'incorrect-prediction';
        gameCard.className = `bg-white rounded-lg shadow game-card ${predictionBorderClass}`;

        const awayProb = (game.away_team.win_probability * 100);
        const homeProb = (game.home_team.win_probability * 100);

        gameCard.innerHTML = `
            <div class="p-4 border-b border-gray-200">
                <div class="flex justify-between items-center text-xs text-gray-500">
                    <span>${game.name}</span>
                    <span>${game.status || 'Scheduled'}</span>
                </div>
            </div>
            <div class="p-4">
                <div class="grid grid-cols-3 items-center text-center">
                    <div class="flex flex-col items-center">
                        <img src="${game.away_team.logo}" alt="${game.away_team.abbreviation}" class="team-logo mb-2" onerror="this.src='https://placehold.co/40x40/cccccc/ffffff?text=?'">
                        <span class="font-bold text-gray-800">${game.away_team.abbreviation}</span>
                        <span class="text-sm text-gray-500">Away</span>
                    </div>
                    <div class="font-bold text-3xl text-gray-800">
                        ${game.status?.toLowerCase().includes('final') ? `${game.away_team.score} - ${game.home_team.score}` : 'vs'}
                    </div>
                    <div class="flex flex-col items-center">
                        <img src="${game.home_team.logo}" alt="${game.home_team.abbreviation}" class="team-logo mb-2" onerror="this.src='https://placehold.co/40x40/cccccc/ffffff?text=?'">
                        <span class="font-bold text-gray-800">${game.home_team.abbreviation}</span>
                        <span class="text-sm text-gray-500">Home</span>
                    </div>
                </div>
            </div>
            <div class="bg-gray-50 p-3 rounded-b-lg">
                <div class="text-center text-sm mb-2">
                    <span class="font-medium">Prediction: </span>
                    <span class="font-bold text-orange-600">${game.predicted_winner || 'N/A'}</span>
                    ${getPredictionBadge(game)}
                </div>
                <div class="w-full prob-bar-bg rounded-full h-2 flex">
                    <div class="prob-bar-away h-2 rounded-l-full" style="width: ${awayProb}%" title="Away Win Prob: ${awayProb.toFixed(1)}%"></div>
                    <div class="prob-bar-home h-2 rounded-r-full" style="width: ${homeProb}%" title="Home Win Prob: ${homeProb.toFixed(1)}%"></div>
                </div>
            </div>
        `;
        scheduleGrid.appendChild(gameCard);
    });
}

function getPredictionBadge(game) {
    if (game.is_correct === true) return `<span class="ml-2 text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-green-600 bg-green-200">Correct</span>`;
    if (game.is_correct === false) return `<span class="ml-2 text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-red-600 bg-red-200">Incorrect</span>`;
    return '';
}

document.addEventListener('DOMContentLoaded', () => {
    populateSelectors();
    fetchPredictions(); 
});

yearSelect.addEventListener('change', fetchPredictions);
seasontypeSelect.addEventListener('change', () => {
    updateWeekSelector();
    fetchPredictions();
});
weekSelect.addEventListener('change', fetchPredictions);