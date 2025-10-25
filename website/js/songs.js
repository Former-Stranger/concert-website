// JavaScript for songs page

let songsData = null;
let allSongs = [];
let filteredSongs = [];

// Load songs data
async function loadSongs() {
    try {
        const response = await fetch(`data/songs.json?v=${Date.now()}`);
        songsData = await response.json();
        allSongs = songsData.all_songs;
        filteredSongs = [...allSongs];

        renderAllSongs();
        populateArtistDropdowns();
        updateCount();
    } catch (error) {
        console.error('Error loading songs:', error);
    }
}

// Tab switching
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });

    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(`tab-${tabName}`).classList.remove('hidden');

    // Add active class to clicked button
    event.target.classList.add('active');
}

// Render all songs list
function renderAllSongs() {
    const container = document.getElementById('songs-list');

    if (filteredSongs.length === 0) {
        container.innerHTML = '<p class="text-center py-8 opacity-70">No songs found</p>';
        return;
    }

    container.innerHTML = filteredSongs.map((song, index) => `
        <div class="song-item flex justify-between items-center p-4 rounded">
            <div class="flex items-center flex-1">
                <span class="text-2xl font-bold mr-4 min-w-[50px]" style="color: #d4773e; font-family: 'Bebas Neue', cursive;">
                    ${index + 1}
                </span>
                <div class="flex-1">
                    <div class="font-bold text-lg">${song.name}</div>
                    ${song.is_mostly_cover ? '<div class="text-sm" style="color: #c1502e;"><i class="fas fa-record-vinyl mr-1"></i>Mostly heard as cover</div>' : ''}
                </div>
            </div>
            <div class="text-right">
                <span class="badge px-4 py-2 rounded-full text-lg">
                    ${song.times_heard}
                </span>
                <div class="text-xs mt-1 opacity-70">times heard</div>
            </div>
        </div>
    `).join('');
}

// Search songs
function searchSongs() {
    const searchTerm = document.getElementById('song-search').value.toLowerCase();
    filteredSongs = allSongs.filter(song =>
        song.name.toLowerCase().includes(searchTerm)
    );
    renderAllSongs();
    updateCount();
}

// Update count display
function updateCount() {
    document.getElementById('showing-count').textContent = filteredSongs.length;
    document.getElementById('total-count').textContent = allSongs.length;
}

// Populate artist dropdowns
function populateArtistDropdowns() {
    // Opening songs artists
    const openerSelect = document.getElementById('opener-artist-filter');
    const openerArtists = Object.keys(songsData.opening_songs_by_artist).sort();
    openerArtists.forEach(artist => {
        const option = document.createElement('option');
        option.value = artist;
        option.textContent = artist;
        openerSelect.appendChild(option);
    });

    // Closing songs artists
    const closerSelect = document.getElementById('closer-artist-filter');
    const closerArtists = Object.keys(songsData.closing_songs_by_artist).sort();
    closerArtists.forEach(artist => {
        const option = document.createElement('option');
        option.value = artist;
        option.textContent = artist;
        closerSelect.appendChild(option);
    });

    // Encore songs artists
    const encoreSelect = document.getElementById('encore-artist-filter');
    const encoreArtists = Object.keys(songsData.encore_songs_by_artist).sort();
    encoreArtists.forEach(artist => {
        const option = document.createElement('option');
        option.value = artist;
        option.textContent = artist;
        encoreSelect.appendChild(option);
    });
}

// Show opening songs for artist
function showOpeningSongs() {
    const artist = document.getElementById('opener-artist-filter').value;
    const container = document.getElementById('opening-songs-list');

    if (!artist) {
        container.innerHTML = '<p class="text-center py-8 opacity-70">Select an artist to see their opening songs</p>';
        return;
    }

    const songs = songsData.opening_songs_by_artist[artist] || [];

    if (songs.length === 0) {
        container.innerHTML = '<p class="text-center py-8 opacity-70">No opening song data for this artist</p>';
        return;
    }

    container.innerHTML = `
        <div class="mb-4 text-center">
            <h3 class="text-2xl font-bold poster-title" style="color: #c1502e;">${artist}</h3>
            <p class="text-sm opacity-70">Most common opening songs</p>
        </div>
        ${songs.map((song, index) => `
            <div class="song-item flex justify-between items-center p-4 rounded">
                <div class="flex items-center flex-1">
                    <span class="text-2xl font-bold mr-4 min-w-[50px]" style="color: #d4773e; font-family: 'Bebas Neue', cursive;">
                        ${index + 1}
                    </span>
                    <div class="font-bold text-lg">${song.song}</div>
                </div>
                <div class="text-right">
                    <span class="badge px-4 py-2 rounded-full text-lg">
                        ${song.times}
                    </span>
                    <div class="text-xs mt-1 opacity-70">times opened</div>
                </div>
            </div>
        `).join('')}
    `;
}

// Show closing songs for artist
function showClosingSongs() {
    const artist = document.getElementById('closer-artist-filter').value;
    const container = document.getElementById('closing-songs-list');

    if (!artist) {
        container.innerHTML = '<p class="text-center py-8 opacity-70">Select an artist to see their closing songs</p>';
        return;
    }

    const songs = songsData.closing_songs_by_artist[artist] || [];

    if (songs.length === 0) {
        container.innerHTML = '<p class="text-center py-8 opacity-70">No closing song data for this artist</p>';
        return;
    }

    container.innerHTML = `
        <div class="mb-4 text-center">
            <h3 class="text-2xl font-bold poster-title" style="color: #c1502e;">${artist}</h3>
            <p class="text-sm opacity-70">Most common closing songs (main set)</p>
        </div>
        ${songs.map((song, index) => `
            <div class="song-item flex justify-between items-center p-4 rounded">
                <div class="flex items-center flex-1">
                    <span class="text-2xl font-bold mr-4 min-w-[50px]" style="color: #d4773e; font-family: 'Bebas Neue', cursive;">
                        ${index + 1}
                    </span>
                    <div class="font-bold text-lg">${song.song}</div>
                </div>
                <div class="text-right">
                    <span class="badge px-4 py-2 rounded-full text-lg">
                        ${song.times}
                    </span>
                    <div class="text-xs mt-1 opacity-70">times closed</div>
                </div>
            </div>
        `).join('')}
    `;
}

// Show encore songs for artist
function showEncoreSongs() {
    const artist = document.getElementById('encore-artist-filter').value;
    const container = document.getElementById('encore-songs-list');

    if (!artist) {
        container.innerHTML = '<p class="text-center py-8 opacity-70">Select an artist to see their encore songs</p>';
        return;
    }

    const songs = songsData.encore_songs_by_artist[artist] || [];

    if (songs.length === 0) {
        container.innerHTML = '<p class="text-center py-8 opacity-70">No encore song data for this artist</p>';
        return;
    }

    container.innerHTML = `
        <div class="mb-4 text-center">
            <h3 class="text-2xl font-bold poster-title" style="color: #c1502e;">${artist}</h3>
            <p class="text-sm opacity-70">Most common encore songs</p>
        </div>
        ${songs.map((song, index) => `
            <div class="song-item flex justify-between items-center p-4 rounded">
                <div class="flex items-center flex-1">
                    <span class="text-2xl font-bold mr-4 min-w-[50px]" style="color: #d4773e; font-family: 'Bebas Neue', cursive;">
                        ${index + 1}
                    </span>
                    <div class="font-bold text-lg">${song.song}</div>
                </div>
                <div class="text-right">
                    <span class="badge px-4 py-2 rounded-full text-lg">
                        ${song.times}
                    </span>
                    <div class="text-xs mt-1 opacity-70">times in encore</div>
                </div>
            </div>
        `).join('')}
    `;
}

// Set up event listeners
document.addEventListener('DOMContentLoaded', () => {
    loadSongs();

    document.getElementById('song-search').addEventListener('input', searchSongs);
    document.getElementById('opener-artist-filter').addEventListener('change', showOpeningSongs);
    document.getElementById('closer-artist-filter').addEventListener('change', showClosingSongs);
    document.getElementById('encore-artist-filter').addEventListener('change', showEncoreSongs);
});
