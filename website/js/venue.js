// JavaScript for venue detail page

// Get venue ID from URL
const urlParams = new URLSearchParams(window.location.search);
const venueId = urlParams.get('id');

// Load venue details
async function loadVenueDetail() {
    if (!venueId) {
        showError('No venue ID provided');
        return;
    }

    try {
        const response = await fetch(`data/venue_details/${venueId}.json`);

        if (!response.ok) {
            showError('Venue not found');
            return;
        }

        const venue = await response.json();
        renderVenueDetail(venue);
    } catch (error) {
        console.error('Error loading venue:', error);
        showError('Error loading venue details');
    }
}

// Render venue details
function renderVenueDetail(venue) {
    // Header
    const header = document.getElementById('venue-header');
    header.innerHTML = `
        <div class="vintage-poster rounded-lg p-10 text-center mb-8">
            <div class="text-5xl mb-4 text-[#f4e4c1]">
                <i class="fas fa-map-marker-alt"></i>
            </div>
            <h2 class="poster-title mb-4 text-[#f4e4c1]" style="font-size: 3.5rem; line-height: 1.1;">${venue.name}</h2>
            <div class="my-6" style="border-top: 2px solid rgba(244, 228, 193, 0.3); border-bottom: 2px solid rgba(244, 228, 193, 0.3); padding: 1.5rem 0;">
                <p class="text-2xl text-[#f4e4c1] font-bold">${venue.city}, ${venue.state}</p>
            </div>
            <p class="poster-title text-[#f4e4c1]" style="font-size: 2.5rem;">${venue.concert_count} Show${venue.concert_count !== 1 ? 's' : ''}</p>
        </div>
    `;

    // Concerts list
    const concertsContainer = document.getElementById('concerts-container');

    if (!venue.concerts || venue.concerts.length === 0) {
        concertsContainer.innerHTML = `
            <div class="text-center py-8 opacity-70">
                <i class="fas fa-info-circle mr-2"></i>
                No concerts found for this venue
            </div>
        `;
        return;
    }

    concertsContainer.innerHTML = `
        <div class="marquee-header text-center text-3xl rounded">
            <i class="fas fa-ticket-alt mr-3"></i>All Shows at This Venue
        </div>
        <div class="space-y-2">
            ${venue.concerts.map(concert => `
                <div class="concert-row flex justify-between items-center p-4 rounded" onclick="window.location.href='concert.html?id=${concert.id}'">
                    <div class="flex-1">
                        <div class="font-bold text-lg">${concert.artists}</div>
                        ${concert.festival_name ? `<div class="text-sm opacity-70">${concert.festival_name}</div>` : ''}
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
    const header = document.getElementById('venue-header');
    header.innerHTML = `
        <div class="text-center py-12">
            <i class="fas fa-exclamation-triangle text-6xl mb-6" style="color: #f87171;"></i>
            <p class="text-2xl font-bold mb-6">${message}</p>
            <a href="venues.html" class="back-link inline-block text-lg font-bold">
                <i class="fas fa-arrow-left mr-2"></i>Return to All Venues
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

// Load venue when page loads
document.addEventListener('DOMContentLoaded', loadVenueDetail);
