// JavaScript for concerts list page

let allConcerts = [];
let filteredConcerts = [];
let concertDetails = new Map(); // Cache for concert details

// Load concerts
async function loadConcerts() {
    try {
        // Add cache-busting parameter to force fresh data
        const response = await fetch(`data/concerts.json?v=${Date.now()}`);
        allConcerts = await response.json();
        filteredConcerts = [...allConcerts];

        populateYearFilter();

        // Restore filters from URL parameters (when returning from concert page)
        const urlParams = new URLSearchParams(window.location.search);
        const yearParam = urlParams.get('year');
        const searchParam = urlParams.get('search');
        const setlistParam = urlParams.get('setlist');

        if (yearParam || searchParam || setlistParam) {
            if (yearParam) {
                document.getElementById('year-filter').value = yearParam;
            }
            if (searchParam) {
                document.getElementById('search').value = searchParam;
            }
            if (setlistParam) {
                document.getElementById('setlist-filter').value = setlistParam;
            }
            applyFilters();
        } else {
            renderConcerts();
            updateCount();
        }
    } catch (error) {
        console.error('Error loading concerts:', error);
    }
}

// Populate year filter dropdown
function populateYearFilter() {
    const years = [...new Set(allConcerts
        .map(c => c.date ? c.date.substring(0, 4) : null)
        .filter(y => y !== null))]
        .sort((a, b) => b - a);

    const select = document.getElementById('year-filter');
    years.forEach(year => {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        select.appendChild(option);
    });
}

// Apply filters
function applyFilters() {
    const searchTerm = document.getElementById('search').value.toLowerCase();
    const yearFilter = document.getElementById('year-filter').value;
    const setlistFilter = document.getElementById('setlist-filter').value;

    console.log('Applying filters:', { searchTerm, yearFilter, setlistFilter });

    // Update URL with current filter state
    updateURLWithFilters(searchTerm, yearFilter, setlistFilter);

    filteredConcerts = allConcerts.filter(concert => {
        // Search filter
        const matchesSearch = !searchTerm ||
            concert.artists.toLowerCase().includes(searchTerm) ||
            concert.venue.toLowerCase().includes(searchTerm) ||
            concert.city.toLowerCase().includes(searchTerm) ||
            (concert.date && concert.date.includes(searchTerm));

        // Year filter
        const matchesYear = !yearFilter || (concert.date && concert.date.startsWith(yearFilter));

        // Setlist filter
        let matchesSetlist = true;
        if (setlistFilter === 'with-setlist') {
            matchesSetlist = concert.hasSetlist === true;
        } else if (setlistFilter === 'no-setlist') {
            matchesSetlist = concert.hasSetlist === false;
        }

        return matchesSearch && matchesYear && matchesSetlist;
    });

    renderConcerts();
    updateCount();
}

// Update URL with current filter state (without page reload)
function updateURLWithFilters(searchTerm, yearFilter, setlistFilter) {
    const params = new URLSearchParams();

    if (searchTerm) params.set('search', searchTerm);
    if (yearFilter) params.set('year', yearFilter);
    if (setlistFilter && setlistFilter !== 'all') params.set('setlist', setlistFilter);

    const newURL = params.toString() ? `?${params.toString()}` : 'concerts.html';
    window.history.replaceState({}, '', newURL);
}

// Build return URL with current filters
function buildReturnURL() {
    // Use current URL as source of truth for filters
    const currentParams = new URLSearchParams(window.location.search);

    // If there are any params, return the full URL, otherwise just concerts.html
    return currentParams.toString() ? `concerts.html?${currentParams.toString()}` : 'concerts.html';
}

// Render concerts table
function renderConcerts() {
    const tbody = document.getElementById('concerts-list');

    if (filteredConcerts.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-8 opacity-70">
                    <i class="fas fa-search mr-2"></i>No concerts found
                </td>
            </tr>
        `;
        return;
    }

    // Build return URL once with current filters
    const returnURL = buildReturnURL();

    tbody.innerHTML = filteredConcerts.map(concert => `
        <tr class="concert-row rounded" onclick="window.location.href='concert.html?id=${concert.id}&returnUrl=${encodeURIComponent(returnURL)}'">
            <td style="font-weight: bold; color: #c1502e;">${formatDate(concert.date)}</td>
            <td class="font-bold">${concert.artists}</td>
            <td>${concert.venue}</td>
            <td>${concert.city}, ${concert.state}</td>
            <td class="text-center">
                ${concert.hasSetlist
                    ? '<i class="fas fa-check-circle" style="color: #4ade80;" title="Setlist available"></i>'
                    : '<i class="fas fa-times-circle" style="color: #f87171;" title="No setlist"></i>'}
            </td>
        </tr>
    `).join('');
}

// Update count display
function updateCount() {
    document.getElementById('showing-count').textContent = filteredConcerts.length;
    document.getElementById('total-count').textContent = allConcerts.length;
}

// Utility function to format date
function formatDate(dateStr) {
    if (!dateStr) return 'Unknown';
    // Parse as local date to avoid timezone issues
    const [year, month, day] = dateStr.split('-');
    const date = new Date(year, month - 1, day);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Set up event listeners
document.addEventListener('DOMContentLoaded', () => {
    loadConcerts();

    document.getElementById('search').addEventListener('input', applyFilters);
    document.getElementById('year-filter').addEventListener('change', applyFilters);
    document.getElementById('setlist-filter').addEventListener('change', applyFilters);
});
