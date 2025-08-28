import { onAuthStateChanged } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js";
import { ref, get, set } from "https://www.gstatic.com/firebasejs/12.1.0/firebase-database.js";
import { auth, database } from './firebase.js';

const gameContent = document.getElementById('game-content');
const weekTitle = document.getElementById('week-display-title');
const prevWeekBtn = document.getElementById('prev-week-btn');
const nextWeekBtn = document.getElementById('next-week-btn');

let nflDivisions = [];
let currentUser = null;
let currentNFLYear, currentNFLWeek, viewedWeek;

async function initializePage() {
    await fetchDivisionData();
    try {
        const weekResponse = await fetch('/api/nfl_week');
        const weekData = await weekResponse.json();
        currentNFLYear = weekData.year;
        currentNFLWeek = weekData.week;
        viewedWeek = currentNFLWeek; // Start by viewing the current week
        
        await displayWeek(viewedWeek);
    } catch (e) {
        console.error("Could not fetch current week.", e);
        weekTitle.textContent = "Error";
    }
}

async function displayWeek(week) {
    if (!currentUser || !nflDivisions.length) return;
    
    viewedWeek = week;
    weekTitle.textContent = `Week ${viewedWeek} (${currentNFLYear})`;
    gameContent.innerHTML = `<p class="text-center py-8">Loading week ${viewedWeek} games...</p>`;

    try {
        const scheduleResponse = await fetch(`/api/lms_schedule/${currentNFLYear}/${viewedWeek}`);
        if (!scheduleResponse.ok) throw new Error('Failed to fetch schedule');
        const scheduleData = await scheduleResponse.json();
        
        // Determine if the week is locked by game time
        let firstGameTime = null;
        if (scheduleData.games.length > 0) {
            const gameTimes = scheduleData.games.map(game => new Date(game.date).getTime());
            firstGameTime = new Date(Math.min(...gameTimes));
        }
        const isLockedByTime = firstGameTime ? new Date() >= firstGameTime : false;

        const gameRef = ref(database, `last_man_standing/${currentNFLYear}/${currentUser.uid}`);
        const gameSnapshot = await get(gameRef);
        const gameData = gameSnapshot.exists() ? gameSnapshot.val() : { status: 'active', picks: {} };

        // --- NEW: SEQUENTIAL PICK LOGIC ---
        const madePicksForWeeks = Object.keys(gameData.picks || {}).map(Number);
        const latestPickWeek = madePicksForWeeks.length > 0 ? Math.max(...madePicksForWeeks) : 0;
        const nextRequiredWeek = latestPickWeek + 1;
        // --- END NEW ---

        // Update nav buttons with the new sequential rule
        prevWeekBtn.disabled = (viewedWeek <= 1);
        nextWeekBtn.disabled = (viewedWeek >= 18 || viewedWeek >= nextRequiredWeek);

        renderGame(scheduleData.games, gameData, currentNFLYear, viewedWeek, isLockedByTime, nextRequiredWeek);
    } catch (error) {
        console.error("Error loading game:", error);
        gameContent.innerHTML = `<div class="text-center text-red-600 p-8">Could not load game schedule for Week ${viewedWeek}.</div>`;
    }
}

function renderGame(games, gameData, year, week, isLockedByTime, nextRequiredWeek) {
    const isLockedSequentially = week > nextRequiredWeek;
    const isLocked = isLockedByTime || isLockedSequentially;

    const teamToDivisionMap = new Map(nflDivisions.map(d => [d.Team_Abv, `${d.Conference} ${d.Division}`]));
    
    const sortedPicks = Object.entries(gameData.picks || {}).sort(([weekA], [weekB]) => parseInt(weekA) - parseInt(weekB));
    const previouslyPickedTeams = sortedPicks.map(([, pick]) => pick && (pick.team || pick)).filter(Boolean);

    const totalPicks = previouslyPickedTeams.length;
    const picksInCurrentCycle = totalPicks % 8;
    const isNewCycle = totalPicks > 0 && picksInCurrentCycle === 0;

    let usedDivisionsThisCycle = new Set();
    if (!isNewCycle) {
        const cycleStartIndex = totalPicks - picksInCurrentCycle;
        const picksThisCycle = previouslyPickedTeams.slice(cycleStartIndex);
        picksThisCycle.forEach(team => {
            if (teamToDivisionMap.has(team)) usedDivisionsThisCycle.add(teamToDivisionMap.get(team));
        });
    }

    const currentPickData = gameData.picks?.[week] || null;
    const currentPickForWeek = currentPickData && typeof currentPickData === 'object' ? currentPickData.team : currentPickData;
    // --- NEW: Get the result of the pick for this week ---
    const pickResult = currentPickData && typeof currentPickData === 'object' ? currentPickData.result : null;

    let statusNotice = '';
    if (isLockedByTime) {
        statusNotice = `<p class="text-center text-blue-600 font-semibold mb-4">This week is now locked. Picks can no longer be made or changed.</p>`;
    } else if (isLockedSequentially) {
        statusNotice = `<p class="text-center text-yellow-600 font-semibold mb-4">You must make a pick for Week ${nextRequiredWeek} before you can pick for this week.</p>`;
    } else if (gameData.status !== 'active') {
        statusNotice = `<p class="text-center text-red-600 font-semibold mb-4">You no longer have a perfect record, but you can keep playing!</p>`;
    }

    let scheduleHtml = `<div class="bg-white p-6 rounded-lg shadow">
                            ${statusNotice}
                            <div id="user-pick-status" class="mb-4"></div>
                            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">`;
    
     games.forEach(game => {
        const homeTeam = game.home_team.abbreviation;
        const awayTeam = game.away_team.abbreviation;
        
        // --- NEW: Determine the highlight class for the card ---
        let resultHighlightClass = '';
        if (currentPickForWeek && (homeTeam === currentPickForWeek || awayTeam === currentPickForWeek)) {
            if (pickResult === 'correct') {
                resultHighlightClass = 'lms-correct-pick';
            } else if (pickResult === 'incorrect') {
                resultHighlightClass = 'lms-incorrect-pick';
            }
        }
        
        const homeTeamDivision = teamToDivisionMap.get(homeTeam);
        const awayTeamDivision = teamToDivisionMap.get(awayTeam);
        const isHomePickedPreviously = previouslyPickedTeams.includes(homeTeam);
        const isAwayPickedPreviously = previouslyPickedTeams.includes(awayTeam);
        const isHomeDivisionUsed = !isNewCycle && usedDivisionsThisCycle.has(homeTeamDivision);
        const isAwayDivisionUsed = !isNewCycle && usedDivisionsThisCycle.has(awayTeamDivision);
        const isHomeSelected = currentPickForWeek === homeTeam;
        const isAwaySelected = currentPickForWeek === awayTeam;
        const awayButtonDisabled = isLocked || isAwayPickedPreviously || isAwayDivisionUsed;
        const homeButtonDisabled = isLocked || isHomePickedPreviously || isHomeDivisionUsed;
        let awayButtonText = 'Pick';
        if (isLocked) awayButtonText = 'Locked';
        else if (isAwayPickedPreviously) awayButtonText = 'Picked';
        else if (isAwayDivisionUsed) awayButtonText = 'Division Used';
        let homeButtonText = 'Pick';
        if (isLocked) homeButtonText = 'Locked';
        else if (isHomePickedPreviously) homeButtonText = 'Picked';
        else if (isHomeDivisionUsed) homeButtonText = 'Division Used';
        const awayButtonClasses = `mt-2 px-3 py-1 text-sm rounded-md ${isAwaySelected ? 'bg-orange-500 text-white' : 'bg-gray-200'} ${awayButtonDisabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-300'}`;
        const homeButtonClasses = `mt-2 px-3 py-1 text-sm rounded-md ${isHomeSelected ? 'bg-orange-500 text-white' : 'bg-gray-200'} ${homeButtonDisabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-300'}`;
        
        // --- UPDATED: Add the resultHighlightClass to the card ---
        scheduleHtml += `<div class="lms-game-card game-card rounded-lg overflow-hidden ${resultHighlightClass}">
            <div class="p-4">
            <div class="grid grid-cols-3 items-center text-center">
            <div class="flex flex-col items-center"><img src="${game.away_team.logo}" alt="${awayTeam}" class="team-logo mb-2"><span class="font-bold text-gray-800">${awayTeam}</span><button class="${awayButtonClasses}" data-team="${awayTeam}" ${awayButtonDisabled ? 'disabled' : ''}>${awayButtonText}</button></div>
            <div class="font-bold text-2xl text-gray-800">vs</div>
            <div class="flex flex-col items-center"><img src="${game.home_team.logo}" alt="${homeTeam}" class="team-logo mb-2"><span class="font-bold text-gray-800">${homeTeam}</span><button class="${homeButtonClasses}" data-team="${homeTeam}" ${homeButtonDisabled ? 'disabled' : ''}>${homeButtonText}</button></div>
            </div></div></div>`;
    });

    scheduleHtml += `</div></div>`;
    gameContent.innerHTML = scheduleHtml;
    
    // ... (rest of the function is the same) ...
    const statusDiv = document.getElementById('user-pick-status');
    if (currentPickForWeek) {
        statusDiv.innerHTML = `<p class="text-lg text-center font-semibold">Your pick for Week ${week}: <span class="text-orange-600">${currentPickForWeek}</span></p>`;
    } else if (!isLocked) {
        statusDiv.innerHTML = `<p class="text-lg text-center text-gray-600">You have not made a pick for Week ${week} yet.</p>`;
    }

    document.querySelectorAll('.lms-game-card button[data-team]').forEach(button => {
        button.addEventListener('click', (e) => {
            const teamAbv = e.target.dataset.team;
            makePick(currentUser.uid, year, week, teamAbv);
        });
    });
}

async function makePick(userId, year, week, teamAbv) {
    const gameRef = ref(database, `last_man_standing/${year}/${userId}`);
    const gameSnapshot = await get(gameRef);
    const gameData = gameSnapshot.exists() ? gameSnapshot.val() : {};

    // --- CORRECTED SEQUENTIAL PICK VALIDATION ---
    const madePicksForWeeks = Object.keys(gameData.picks || {}).map(Number);
    const hasPickForThisWeek = madePicksForWeeks.includes(week);
    const latestPickWeek = madePicksForWeeks.length > 0 ? Math.max(...madePicksForWeeks) : 0;
    const nextRequiredWeek = latestPickWeek + 1;

    // A pick is invalid ONLY IF a pick for this week does NOT exist yet, 
    // AND this week is NOT the next one in the sequence.
    if (!hasPickForThisWeek && week !== nextRequiredWeek) {
        alert(`You must make your picks in order. Please make a pick for Week ${nextRequiredWeek} first.`);
        return;
    }
    // --- END CORRECTION ---

    // Re-check time lock before saving
    const scheduleResponse = await fetch(`/api/lms_schedule/${year}/${week}`);
    const scheduleData = await scheduleResponse.json();
    let firstGameTime = null;
    if (scheduleData.games.length > 0) {
        const gameTimes = scheduleData.games.map(game => new Date(game.date).getTime());
        firstGameTime = new Date(Math.min(...gameTimes));
    }
    if (firstGameTime && new Date() >= firstGameTime) {
        alert("This week is locked. Your pick cannot be saved.");
        displayWeek(week);
        return;
    }

    // Validation for team/division picks is the same
    const teamToDivisionMap = new Map(nflDivisions.map(d => [d.Team_Abv, `${d.Conference} ${d.Division}`]));
    const sortedPicks = Object.entries(gameData.picks || {}).sort(([weekA], [weekB]) => parseInt(weekA) - parseInt(weekB));
    const previouslyPickedTeams = sortedPicks.map(([, pick]) => pick && (pick.team || pick)).filter(Boolean);
    
    // When changing a pick, we must not count the original pick as "previously picked"
    const otherPickedTeams = previouslyPickedTeams.filter(team => {
        const pickForWeek = gameData.picks[week];
        // If there's a pick for this week, don't include it in the "already picked" list
        if (pickForWeek && pickForWeek.team === team) {
            return false;
        }
        return true;
    });

    if (otherPickedTeams.includes(teamAbv)) {
        alert("You have already picked this team in a previous week.");
        return;
    }

    const totalPicks = previouslyPickedTeams.length;
    const picksInCurrentCycle = totalPicks % 8;
    const isNewCycle = totalPicks > 0 && picksInCurrentCycle === 0;
    let usedDivisionsThisCycle = new Set();
    if (!isNewCycle) {
        const cycleStartIndex = totalPicks - picksInCurrentCycle;
        const picksThisCycle = previouslyPickedTeams.slice(cycleStartIndex);
        picksThisCycle.forEach(team => {
            if (teamToDivisionMap.has(team)) usedDivisionsThisCycle.add(teamToDivisionMap.get(team));
        });
    }

    // When changing a pick, we must not count the original division as "used" for this week's check
    const pickForThisWeek = gameData.picks?.[week];
    if (pickForThisWeek) {
        const originalDivision = teamToDivisionMap.get(pickForThisWeek.team);
        if (originalDivision) {
            usedDivisionsThisCycle.delete(originalDivision);
        }
    }
    
    const teamDivision = teamToDivisionMap.get(teamAbv);
    if (!isNewCycle && usedDivisionsThisCycle.has(teamDivision)) {
        alert("You have already picked a team from this division in the current cycle.");
        return;
    }

    const pickRef = ref(database, `last_man_standing/${year}/${userId}/picks/${week}`);
    try {
        const pickData = { team: teamAbv, result: 'unknown' };
        await set(pickRef, pickData);
        displayWeek(week);
    } catch (error) {
        console.error("Failed to save pick:", error);
        alert("There was an error saving your pick.");
    }
}

// --- INITIALIZATION AND EVENT LISTENERS ---
async function fetchDivisionData() {
    if (nflDivisions.length > 0) return;
    try {
        const response = await fetch('/api/nfl_divisions');
        nflDivisions = await response.json();
    } catch (e) {
        console.error("Failed to load NFL division data", e);
    }
}

onAuthStateChanged(auth, (user) => {
    if (user) {
        currentUser = user;
        initializePage();
    } else {
        currentUser = null;
        gameContent.innerHTML = `<div class="text-center bg-white p-8 rounded-lg shadow"><h2 class="text-xl font-bold">Please log in to play</h2><p class="mt-2">You need to be logged in to participate in the Last Man Standing game.</p><a href="/login" class="mt-4 inline-block bg-orange-500 text-white px-6 py-2 rounded-md hover:bg-orange-600">Login</a></div>`;
        weekTitle.textContent = "Last Man Standing";
        prevWeekBtn.disabled = true;
        nextWeekBtn.disabled = true;
    }
});

prevWeekBtn.addEventListener('click', () => {
    if (viewedWeek > 1) {
        displayWeek(viewedWeek - 1);
    }
});
nextWeekBtn.addEventListener('click', () => {
    if (viewedWeek < 18) {
        displayWeek(viewedWeek + 1);
    }
});