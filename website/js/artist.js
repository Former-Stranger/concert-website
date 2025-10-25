// JavaScript for artist detail page

// Get artist ID from URL
const urlParams = new URLSearchParams(window.location.search);
const artistId = urlParams.get('id');

// Load artist details
async function loadArtistDetail() {
    if (!artistId) {
        showError('No artist ID provided');
        return;
    }

    try {
        const response = await fetch(`data/artist_details/${artistId}.json?v=${Date.now()}`);

        if (!response.ok) {
            showError('Artist not found');
            return;
        }

        const artist = await response.json();
        renderArtistDetail(artist);
    } catch (error) {
        console.error('Error loading artist:', error);
        showError('Error loading artist details');
    }
}

// Render artist details
function renderArtistDetail(artist) {
    // Header
    const header = document.getElementById('artist-header');
    header.innerHTML = `
        <div class="vintage-poster rounded-lg p-10 text-center mb-8">
            <div class="text-5xl mb-4 text-[#f4e4c1]">
                <i class="fas fa-microphone"></i>
            </div>
            <h2 class="poster-title mb-4 text-[#f4e4c1]" style="font-size: 3.5rem; line-height: 1.1;">${artist.name}</h2>
            <div class="my-6" style="border-top: 2px solid rgba(244, 228, 193, 0.3); border-bottom: 2px solid rgba(244, 228, 193, 0.3); padding: 1.5rem 0;">
                <p class="text-2xl text-[#f4e4c1] font-bold">Live in Concert</p>
            </div>
            <p class="poster-title text-[#f4e4c1]" style="font-size: 2.5rem;">${artist.concert_count} Show${artist.concert_count !== 1 ? 's' : ''}</p>
        </div>
    `;

    // Concerts list
    const concertsContainer = document.getElementById('concerts-container');

    if (!artist.concerts || artist.concerts.length === 0) {
        concertsContainer.innerHTML = `
            <div class="text-center py-8 opacity-70">
                <i class="fas fa-info-circle mr-2"></i>
                No concerts found for this artist
            </div>
        `;
        return;
    }

    // Top songs section (if available)
    let topSongsHtml = '';
    if (artist.top_songs && artist.top_songs.length > 0) {
        topSongsHtml = `
            <div class="mb-8">
                <div class="marquee-header text-center text-3xl rounded">
                    <i class="fas fa-music mr-3"></i>Top 10 Songs
                </div>
                <div class="space-y-2">
                    ${artist.top_songs.map((song, index) => `
                        <div class="concert-row flex justify-between items-center p-4 rounded">
                            <div class="flex items-center flex-1">
                                <span class="text-2xl font-bold mr-4 min-w-[50px]" style="color: #d4773e; font-family: 'Bebas Neue', cursive;">
                                    ${index + 1}
                                </span>
                                <div class="font-bold text-lg">${song.name}</div>
                            </div>
                            <div class="text-right">
                                <span class="text-2xl font-bold" style="color: #c1502e; font-family: 'Bebas Neue', cursive;">
                                    ${song.times_played}
                                </span>
                                <div class="text-xs opacity-70">times played</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    concertsContainer.innerHTML = `
        ${topSongsHtml}
        <div class="marquee-header text-center text-3xl rounded">
            <i class="fas fa-ticket-alt mr-3"></i>All Shows
        </div>
        <div class="space-y-2">
            ${artist.concerts.map(concert => `
                <div class="concert-row flex justify-between items-center p-4 rounded" onclick="window.location.href='concert.html?id=${concert.id}'">
                    <div class="flex-1">
                        ${concert.festival_name ? `<div class="text-sm font-bold" style="color: #c1502e;">${concert.festival_name}</div>` : ''}
                        <div class="font-bold text-lg">${concert.venue}</div>
                        <div class="text-sm opacity-70">${concert.city}, ${concert.state}</div>
                    </div>
                    <div class="text-right">
                        <div class="font-bold" style="color: #c1502e;">${formatDate(concert.date)}</div>
                        <div class="text-xs opacity-70">Show #${concert.show_number}</div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// Show error message
function showError(message) {
    const header = document.getElementById('artist-header');
    header.innerHTML = `
        <div class="text-center py-12">
            <i class="fas fa-exclamation-triangle text-6xl mb-6" style="color: #f87171;"></i>
            <p class="text-2xl font-bold mb-6">${message}</p>
            <a href="artists.html" class="back-link inline-block text-lg font-bold">
                <i class="fas fa-arrow-left mr-2"></i>Return to All Artists
            </a>
        </div>
    `;
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

// Load artist when page loads
document.addEventListener('DOMContentLoaded', loadArtistDetail);
