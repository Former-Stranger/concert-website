-- Table to store pending setlist submissions awaiting admin approval
CREATE TABLE IF NOT EXISTS pending_setlist_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concert_id INTEGER NOT NULL,
    setlistfm_url TEXT NOT NULL,
    setlistfm_id TEXT NOT NULL,
    submitted_by_email TEXT,
    submitted_by_name TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending', -- pending, approved, rejected
    reviewed_by_email TEXT,
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    -- Store the fetched setlist data as JSON for preview before approval
    setlist_data TEXT, -- JSON string
    FOREIGN KEY (concert_id) REFERENCES concerts(id),
    UNIQUE(concert_id, setlistfm_id) -- Prevent duplicate submissions for same concert
);

CREATE INDEX IF NOT EXISTS idx_pending_submissions_concert ON pending_setlist_submissions(concert_id);
CREATE INDEX IF NOT EXISTS idx_pending_submissions_status ON pending_setlist_submissions(status);
CREATE INDEX IF NOT EXISTS idx_pending_submissions_submitted_at ON pending_setlist_submissions(submitted_at);
