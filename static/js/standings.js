const yearSelect = document.getElementById('year-select');
const seasontypeSelect = document.getElementById('seasontype-select');

function populateSelectors() {
    const currentYear = new Date().getFullYear();
    const selectedYear = yearSelect.dataset.selected;

    for (let year = currentYear; year >= 2022; year--) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        if (year == selectedYear) {
            option.selected = true;
        }
        yearSelect.appendChild(option);
    }
    
    seasontypeSelect.value = seasontypeSelect.dataset.selected;
}

function navigateToStandings() {
    const year = yearSelect.value;
    const seasontype = seasontypeSelect.value;
    window.location.href = `/standings/${year}/${seasontype}`;
}

document.addEventListener('DOMContentLoaded', populateSelectors);
yearSelect.addEventListener('change', navigateToStandings);
seasontypeSelect.addEventListener('change', navigateToStandings);