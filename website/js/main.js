// Main JavaScript for home page

let stats = null;
let concerts = null;

// Load data
async function loadData() {
    try {
        // Load stats
        const statsResponse = await fetch(`data/stats.json?v=${Date.now()}`);
        stats = await statsResponse.json();

        // Load concerts
        const concertsResponse = await fetch(`data/concerts.json?v=${Date.now()}`);
        concerts = await concertsResponse.json();

        // Populate page
        populateStats();
        populateTopArtists();
        populateTopVenues();
        populateRecentConcerts();
        populateOnThisDate();
        populateYearGrid();
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

// Populate main stats
function populateStats() {
    document.getElementById('total-concerts').textContent = stats.total_concerts.toLocaleString();
    document.getElementById('total-artists').textContent = stats.total_artists.toLocaleString();
    document.getElementById('total-venues').textContent = stats.total_venues.toLocaleString();
    document.getElementById('total-songs').textContent = stats.total_songs.toLocaleString();
    document.getElementById('last-updated').textContent = new Date(stats.generated_at).toLocaleDateString();
}

// Populate top artists
function populateTopArtists() {
    const container = document.getElementById('top-artists');
    container.innerHTML = stats.top_artists.map((artist, index) => `
        <div class="top-item flex justify-between items-center py-3 px-4 rounded">
            <div class="flex items-center">
                <span class="text-3xl font-bold mr-4" style="color: #d4773e; font-family: 'Bebas Neue', cursive;">${index + 1}</span>
                <span class="font-semibold">${artist.name}</span>
            </div>
            <span class="badge px-3 py-1 rounded-full text-sm font-bold">${artist.count} shows</span>
        </div>
    `).join('');
}

// Populate top venues
function populateTopVenues() {
    const container = document.getElementById('top-venues');
    container.innerHTML = stats.top_venues.map((venue, index) => `
        <div class="top-item flex justify-between items-center py-3 px-4 rounded">
            <div class="flex items-center">
                <span class="text-3xl font-bold mr-4" style="color: #d4773e; font-family: 'Bebas Neue', cursive;">${index + 1}</span>
                <span class="font-semibold">${venue.name}</span>
            </div>
            <span class="badge px-3 py-1 rounded-full text-sm font-bold">${venue.count} shows</span>
        </div>
    `).join('');
}

// Populate recent concerts
function populateRecentConcerts() {
    const container = document.getElementById('recent-concerts');
    const recentConcerts = concerts.slice(0, 10);

    container.innerHTML = recentConcerts.map(concert => `
        <div class="concert-item flex justify-between items-center py-4 px-4 rounded">
            <div>
                <div class="font-bold text-lg">${concert.artists}</div>
                <div class="text-sm opacity-70">${concert.venue} - ${concert.city}, ${concert.state}</div>
            </div>
            <div class="text-right">
                <div class="font-bold" style="color: #d4773e;">${formatDate(concert.date)}</div>
                <a href="concert.html?id=${concert.id}" class="text-sm hover:underline" style="color: #c1502e;">View Details →</a>
            </div>
        </div>
    `).join('');
}

// On This Date feature
function populateOnThisDate() {
    const today = new Date();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const todayStr = `${month}-${day}`;

    const matchingConcerts = concerts.filter(concert => {
        if (!concert.date) return false;
        const concertDate = concert.date.substring(5); // Get MM-DD
        return concertDate === todayStr;
    });

    const container = document.getElementById('on-this-date-content');

    if (matchingConcerts.length === 0) {
        container.innerHTML = `
            <p class="text-center opacity-70">
                <i class="fas fa-calendar-times mr-2"></i>
                No concerts on this date in your history
            </p>
        `;
    } else {
        container.innerHTML = matchingConcerts.map(concert => {
            const year = concert.date.substring(0, 4);
            const yearsAgo = today.getFullYear() - parseInt(year);

            return `
                <div class="concert-item py-4 px-4 rounded mb-3">
                    <div class="flex justify-between items-start">
                        <div>
                            <div class="text-xl font-bold">${concert.artists}</div>
                            <div class="opacity-70 text-sm">${concert.venue} - ${concert.city}, ${concert.state}</div>
                        </div>
                        <div class="text-right">
                            <div class="text-3xl font-bold" style="color: #d4773e; font-family: 'Bebas Neue', cursive;">${year}</div>
                            <div class="text-sm opacity-70">${yearsAgo} year${yearsAgo !== 1 ? 's' : ''} ago</div>
                        </div>
                    </div>
                    <a href="concert.html?id=${concert.id}" class="hover:underline mt-2 inline-block" style="color: #c1502e; font-weight: bold;">
                        View Details →
                    </a>
                </div>
            `;
        }).join('');
    }
}

// Populate year grid with compact cards
function populateYearGrid() {
    const container = document.getElementById('year-grid');

    // Sort by year descending (most recent first)
    const yearData = [...stats.concerts_by_year].sort((a, b) => b.year - a.year);

    // Find max count for scaling the visual indicator
    const maxCount = Math.max(...yearData.map(d => d.count));

    container.innerHTML = yearData.map(data => {
        const percentage = (data.count / maxCount) * 100;

        return `
            <div class="relative p-4 rounded-lg transition-all duration-300"
                 style="background: linear-gradient(135deg, rgba(212, 119, 62, ${0.1 + (percentage / 200)}) 0%, rgba(193, 80, 46, ${0.1 + (percentage / 200)}) 100%); border: 2px solid #d4773e; cursor: pointer;"
                 onclick="window.location.href='concerts.html?year=${data.year}';"
                 onmouseover="this.style.transform='translateY(-3px)'; this.style.borderColor='#c1502e';"
                 onmouseout="this.style.transform='translateY(0)'; this.style.borderColor='#d4773e';">
                <div class="text-center">
                    <div class="poster-title text-3xl mb-1" style="color: #c1502e; font-family: 'Bebas Neue', cursive;">${data.year}</div>
                    <div class="text-2xl font-bold" style="color: #2d1b1b;">${data.count}</div>
                    <div class="text-xs uppercase tracking-wider font-bold opacity-60">show${data.count !== 1 ? 's' : ''}</div>
                </div>
                <!-- Visual indicator bar -->
                <div class="mt-3 h-1 rounded-full overflow-hidden" style="background: rgba(45, 27, 27, 0.2);">
                    <div class="h-full rounded-full" style="width: ${percentage}%; background: linear-gradient(90deg, #d4773e 0%, #c1502e 100%);"></div>
                </div>
            </div>
        `;
    }).join('');
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

// Load data when page loads
document.addEventListener('DOMContentLoaded', loadData);
