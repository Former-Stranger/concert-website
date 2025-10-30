// JavaScript for concert detail page

// Get concert ID from URL
const urlParams = new URLSearchParams(window.location.search);
const concertId = urlParams.get('id');

// Load concert details
async function loadConcertDetail() {
    if (!concertId) {
        showError('No concert ID provided');
        return;
    }

    // Try to load detailed concert info first
    const detailResponse = await fetch(`data/concert_details/${concertId}.json?v=${Date.now()}`);

    // Try to parse the response as JSON
    let concert = null;
    let hasSetlist = false;

    if (detailResponse.ok) {
        try {
            const text = await detailResponse.text();
            // Check if it's actually JSON (not HTML)
            if (text.trim().startsWith('{')) {
                concert = JSON.parse(text);
                hasSetlist = true;
            }
        } catch (error) {
            console.log('Could not parse concert detail as JSON, will load basic info');
        }
    }

    if (hasSetlist && concert) {
        // Has setlist - render full details
        renderConcertDetail(concert);
    } else {
        // No setlist - load basic info from concerts.json
        console.log('No setlist found, loading basic concert info for ID:', concertId);

        try {
            const concertsResponse = await fetch(`data/concerts.json?v=${Date.now()}`);

            if (!concertsResponse.ok) {
                console.error('Failed to load concerts.json');
                showError('Error loading concert data');
                return;
            }

            const allConcerts = await concertsResponse.json();
            console.log('Loaded concerts.json, searching for concert ID:', concertId);
            const basicConcert = allConcerts.find(c => c.id === concertId);

            if (basicConcert) {
                console.log('Found basic concert:', basicConcert);
                renderBasicConcert(basicConcert);
            } else {
                console.error('Concert not found in concerts.json');
                showError('Concert not found');
            }
        } catch (error) {
            console.error('Error loading basic concert info:', error);
            showError('Error loading concert details');
        }
    }
}

// Render concert details
function renderConcertDetail(concert) {
    // Get headliners and openers
    const headliners = concert.artists ? concert.artists.filter(a => a.role === 'headliner' || a.role === 'festival_performer') : [];
    const openers = concert.artists ? concert.artists.filter(a => a.role === 'opener') : [];

    // Determine if this is a multi-setlist concert (co-headliners)
    const hasMultipleSetlists = concert.setlists && concert.setlists.length > 1;

    // Calculate stats based on single or multiple setlists
    const songCount = hasMultipleSetlists ? concert.total_song_count : concert.song_count;
    const hasEncore = concert.has_encore;
    const allSongs = hasMultipleSetlists
        ? concert.setlists.flatMap(s => s.songs)
        : (concert.songs || []);

    // Header
    const header = document.getElementById('concert-header');
    header.innerHTML = `
        <div class="vintage-poster rounded-lg p-10 text-center mb-8">
            <h2 class="poster-title mb-4 text-[#f4e4c1]" style="font-size: 3.5rem; line-height: 1.1;">${getArtistNames(concert.artists)}</h2>
            ${openers.length > 0 ? `
                <p class="text-xl mb-4 text-[#f4e4c1] opacity-80">
                    with ${openers.map(a => a.name).join(', ')}
                </p>
            ` : ''}
            ${concert.tour_name ? `<p class="text-xl mb-4 text-[#f4e4c1] opacity-80 italic"><i class="fas fa-route mr-2"></i>${concert.tour_name}</p>` : ''}
            ${concert.festival_name ? `<p class="text-2xl mb-4 text-[#f4e4c1] opacity-90">${concert.festival_name}</p>` : ''}
            <div class="my-6" style="border-top: 2px solid rgba(244, 228, 193, 0.3); border-bottom: 2px solid rgba(244, 228, 193, 0.3); padding: 1.5rem 0;">
                <p class="text-2xl text-[#f4e4c1] mb-2 font-bold">${concert.venue}</p>
                <p class="text-xl text-[#f4e4c1] opacity-80">${concert.city}, ${concert.state}</p>
            </div>
            <p class="poster-title text-[#f4e4c1]" style="font-size: 2.5rem;">${formatDate(concert.date)}</p>
        </div>

        <!-- Stats -->
        <div class="grid grid-cols-3 gap-4 mb-6">
            <div class="stat-badge rounded-lg p-4 text-center">
                <div class="poster-title text-4xl mb-2" style="color: #c1502e;">${songCount}</div>
                <div class="text-sm uppercase tracking-wider font-bold opacity-70">Songs Played</div>
            </div>
            <div class="stat-badge rounded-lg p-4 text-center">
                <div class="text-4xl mb-2 ${hasEncore ? '' : 'opacity-30'}" style="color: ${hasEncore ? '#4ade80' : '#2d1b1b'};">
                    ${hasEncore ? '<i class="fas fa-check-circle"></i>' : '<i class="fas fa-times-circle"></i>'}
                </div>
                <div class="text-sm uppercase tracking-wider font-bold opacity-70">Encore</div>
            </div>
            <div class="stat-badge rounded-lg p-4 text-center">
                <div class="poster-title text-4xl mb-2" style="color: #c1502e;">${countCovers(allSongs)}</div>
                <div class="text-sm uppercase tracking-wider font-bold opacity-70">Covers</div>
            </div>
        </div>

        ${concert.setlistfm_url ? `
            <div class="text-center flex flex-col md:flex-row gap-4 justify-center items-center">
                <a href="${concert.setlistfm_url}" target="_blank" class="setlist-fm-btn inline-block px-8 py-3 rounded text-lg">
                    <i class="fas fa-external-link-alt mr-2"></i>View on Setlist.fm
                </a>
                <button id="update-setlist-btn" class="setlist-fm-btn inline-block px-8 py-3 rounded text-lg hidden">
                    <i class="fas fa-edit mr-2"></i>Update Setlist
                </button>
            </div>
        ` : ''}
    `;

    // Setlist
    const setlistContainer = document.getElementById('setlist-container');

    // Check if we have any setlist data
    const hasSongs = hasMultipleSetlists ? allSongs.length > 0 : (concert.songs && concert.songs.length > 0);

    if (!hasSongs) {
        setlistContainer.innerHTML = `
            <div class="text-center py-8 opacity-70">
                <i class="fas fa-info-circle mr-2"></i>
                No setlist available for this concert
            </div>
        `;
        return;
    }

    // Render setlist(s)
    if (hasMultipleSetlists) {
        // Multiple setlists - separate openers from headliners
        const openers = concert.setlists.filter(s => s.artist_role === 'opener');
        const headliners = concert.setlists.filter(s => s.artist_role === 'headliner' || s.artist_role === 'festival_performer');

        const renderSetlist = (setlist, showRole = false) => {
            const songsBySet = groupSongsBySet(setlist.songs);
            return `
                <div class="mb-10">
                    <div class="flex justify-between items-center mb-6">
                        <h3 class="text-3xl font-bold poster-title" style="color: #c1502e;">
                            ${setlist.artist_name}
                            ${showRole && setlist.artist_role === 'opener' ? '<span class="text-lg opacity-70">(opener)</span>' : ''}
                            <span class="text-xl opacity-70">(${setlist.song_count} songs)</span>
                        </h3>
                        ${setlist.setlistfm_url ? `
                            <a href="${setlist.setlistfm_url}" target="_blank" class="setlist-fm-btn inline-block px-4 py-2 rounded text-sm">
                                <i class="fas fa-external-link-alt mr-2"></i>View on Setlist.fm
                            </a>
                        ` : ''}
                    </div>
                    ${Object.entries(songsBySet).map(([setName, songs]) => `
                        <div class="mb-6">
                            <h4 class="text-xl font-bold mb-4 poster-title" style="color: #d4773e;">
                                ${setName}
                                ${songs[0].encore > 0 ? `<span class="text-lg opacity-70">(Encore ${songs[0].encore})</span>` : ''}
                            </h4>
                            <div class="space-y-3">
                                ${songs.map(song => `
                                    <div class="song-item flex items-start p-4 rounded">
                                        <div class="font-bold mr-4 min-w-[40px]" style="color: #d4773e; font-family: 'Bebas Neue', cursive; font-size: 1.5rem;">${song.position}</div>
                                        <div class="flex-1">
                                            <div class="font-bold text-lg">${song.name}</div>
                                            ${song.is_cover && song.cover_artist ? `
                                                <div class="text-sm mt-1 font-semibold" style="color: #c1502e;">
                                                    <i class="fas fa-record-vinyl mr-1"></i>Cover of ${song.cover_artist}
                                                </div>
                                            ` : ''}
                                            ${song.guest_artist ? `
                                                <div class="text-sm mt-1 font-semibold" style="color: #2d1b1b;">
                                                    <i class="fas fa-user-plus mr-1"></i>with ${song.guest_artist}
                                                </div>
                                            ` : ''}
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        };

        setlistContainer.innerHTML = `
            <div class="marquee-header text-center text-3xl rounded mb-6">
                <i class="fas fa-list-ul mr-3"></i>Setlists
            </div>
            ${openers.length > 0 ? `
                <div class="mb-8">
                    <h3 class="text-2xl font-bold mb-4 poster-title" style="color: #4ade80;">
                        <i class="fas fa-play-circle mr-2"></i>Opening Act${openers.length > 1 ? 's' : ''}
                    </h3>
                    ${openers.map(setlist => renderSetlist(setlist, false)).join('<hr class="border-2 border-[#4ade80] opacity-20 my-6">')}
                </div>
                <hr class="border-2 border-[#d4773e] opacity-30 my-10">
            ` : ''}
            ${headliners.map(setlist => renderSetlist(setlist, false)).join('<hr class="border-2 border-[#d4773e] opacity-30 my-8">')}
        `;
    } else {
        // Single setlist (backward compatible)
        const songsBySet = groupSongsBySet(concert.songs);

        setlistContainer.innerHTML = `
            <div class="marquee-header text-center text-3xl rounded">
                <i class="fas fa-list-ul mr-3"></i>Setlist
            </div>
            ${Object.entries(songsBySet).map(([setName, songs]) => `
                <div class="mb-8">
                    <h4 class="text-2xl font-bold mb-4 poster-title" style="color: #c1502e;">
                        ${setName}
                        ${songs[0].encore > 0 ? `<span class="text-lg opacity-70">(Encore ${songs[0].encore})</span>` : ''}
                    </h4>
                    <div class="space-y-3">
                        ${songs.map(song => `
                            <div class="song-item flex items-start p-4 rounded">
                                <div class="font-bold mr-4 min-w-[40px]" style="color: #d4773e; font-family: 'Bebas Neue', cursive; font-size: 1.5rem;">${song.position}</div>
                                <div class="flex-1">
                                    <div class="font-bold text-lg">${song.name}</div>
                                    ${song.is_cover && song.cover_artist ? `
                                        <div class="text-sm mt-1 font-semibold" style="color: #c1502e;">
                                            <i class="fas fa-record-vinyl mr-1"></i>Cover of ${song.cover_artist}
                                        </div>
                                    ` : ''}
                                    ${song.guest_artist ? `
                                        <div class="text-sm mt-1 font-semibold" style="color: #2d1b1b;">
                                            <i class="fas fa-user-plus mr-1"></i>with ${song.guest_artist}
                                        </div>
                                    ` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('')}
        `;
    }
}

// Group songs by set name
function groupSongsBySet(songs) {
    const sets = {};
    for (const song of songs) {
        const setName = song.set_name || 'Main Set';
        if (!sets[setName]) {
            sets[setName] = [];
        }
        sets[setName].push(song);
    }
    return sets;
}

// Get artist names as a string
function getArtistNames(artists) {
    if (!artists || artists.length === 0) return 'Unknown Artist';
    const headliners = artists.filter(a => a.role === 'headliner' || a.role === 'festival_performer');
    return headliners.map(a => a.name).join(', ') || artists[0].name;
}

// Count covers
function countCovers(songs) {
    if (!songs) return 0;
    return songs.filter(s => s.is_cover).length;
}

// Show error message
function showError(message) {
    const header = document.getElementById('concert-header');
    header.innerHTML = `
        <div class="text-center py-12">
            <i class="fas fa-exclamation-triangle text-6xl mb-6" style="color: #f87171;"></i>
            <p class="text-2xl font-bold mb-6">${message}</p>
            <a href="concerts.html" class="setlist-fm-btn inline-block px-8 py-3 rounded text-lg">
                <i class="fas fa-arrow-left mr-2"></i>Return to All Shows
            </a>
        </div>
    `;
}

// Render basic concert info (without setlist)
function renderBasicConcert(concert) {
    // Header
    const header = document.getElementById('concert-header');
    header.innerHTML = `
        <div class="vintage-poster rounded-lg p-10 text-center mb-8">
            <h2 class="poster-title mb-4 text-[#f4e4c1]" style="font-size: 3.5rem; line-height: 1.1;">${concert.artists}</h2>
            ${concert.tour_name ? `<p class="text-xl mb-4 text-[#f4e4c1] opacity-80 italic"><i class="fas fa-route mr-2"></i>${concert.tour_name}</p>` : ''}
            ${concert.festival_name ? `<p class="text-2xl mb-4 text-[#f4e4c1] opacity-90">${concert.festival_name}</p>` : ''}
            <div class="my-6" style="border-top: 2px solid rgba(244, 228, 193, 0.3); border-bottom: 2px solid rgba(244, 228, 193, 0.3); padding: 1.5rem 0;">
                <p class="text-2xl text-[#f4e4c1] mb-2 font-bold">${concert.venue}</p>
                <p class="text-xl text-[#f4e4c1] opacity-80">${concert.city}, ${concert.state}</p>
            </div>
            <p class="poster-title text-[#f4e4c1]" style="font-size: 2.5rem;">${formatDate(concert.date)}</p>
        </div>
    `;

    // No setlist available
    const setlistContainer = document.getElementById('setlist-container');
    setlistContainer.innerHTML = `
        <div class="text-center py-12 bg-[rgba(244,228,193,0.05)] rounded-lg border-2 border-[#d4773e]">
            <i class="fas fa-info-circle text-6xl mb-6" style="color: #d4773e;"></i>
            <p class="text-2xl font-bold mb-2">No Setlist Available</p>
            <p class="opacity-70">We don't currently have a setlist for this show.</p>
        </div>
    `;

    // Show the submit setlist section
    const submitSection = document.getElementById('submit-setlist-section');
    console.log('Submit section element:', submitSection);
    if (submitSection) {
        console.log('Showing submit section...');
        submitSection.classList.remove('hidden');

        // Set the setlist.fm search link
        const findSetlistLink = document.getElementById('find-setlist-link');
        if (findSetlistLink) {
            // Construct search query from concert data with proper URL encoding
            const searchQuery = `${concert.artists} ${concert.venue} ${concert.date}`;
            findSetlistLink.href = `https://www.setlist.fm/search?query=${encodeURIComponent(searchQuery)}`;
        }
    } else {
        console.error('Submit section element not found!');
    }
}

// Show no setlist message
function showNoSetlist() {
    const header = document.getElementById('concert-header');
    header.innerHTML = `
        <div class="text-center py-12">
            <i class="fas fa-info-circle text-6xl mb-6" style="color: #d4773e;"></i>
            <p class="text-2xl font-bold mb-6">No setlist available for this concert</p>
            <a href="concerts.html" class="setlist-fm-btn inline-block px-8 py-3 rounded text-lg">
                <i class="fas fa-arrow-left mr-2"></i>Return to All Shows
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
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Load concert when page loads
document.addEventListener('DOMContentLoaded', loadConcertDetail);
