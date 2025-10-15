#!/usr/bin/env python3
"""
Parse venue notes and extract city, state, and venue_type information
"""

import csv
import re
from pathlib import Path

def parse_venue_info(original_name, notes):
    """Extract city, state, venue_type from notes"""

    # Define venue mappings based on the notes
    # Format: original_name -> (canonical_name, city, state, venue_type, confidence)

    mappings = {
        'Electric Bowery': ('Bowery Electric', 'New York', 'NY', 'club', 100),
        'FYE': (None, None, None, None, 0),  # Not enough info
        'Fairfield Stage One': ('Fairfield Stage One', 'Fairfield', 'CT', 'theater', 100),
        'Farmingville Amphitheater': ('Bald Hill Amphitheater', 'Farmingville', 'NY', 'amphitheater', 100),
        'Foxwoods': ('Foxwoods Resort Casino', 'Mashantucket', 'CT', 'casino', 100),
        'Foxwoods Casino': ('Foxwoods Resort Casino', 'Mashantucket', 'CT', 'casino', 100),
        'Ft. Adams': ('Fort Adams State Park', 'Newport', 'RI', 'outdoor', 100),
        "Garcia's": ("Garcia's at The Capitol Theatre", 'Port Chester', 'NY', 'club', 100),
        'Gibson Guitar Tent (Vegas)': ('Gibson Guitar Tent', 'Las Vegas', 'NV', 'outdoor', 90),
        'Gramercy': ('Gramercy Theatre', 'New York', 'NY', 'theater', 100),
        'Grange Fair': ('Grange Fair', 'Yorktown Heights', 'NY', 'outdoor', 100),
        'Hammerstein Ballroom': ('Hammerstein Ballroom', 'New York', 'NY', 'theater', 100),
        'Hard Rock NYC': ('Hard Rock Hotel New York', 'New York', 'NY', 'club', 100),
        'Hartford': ('XL Center', 'Hartford', 'CT', 'arena', 100),
        'Hartford Covic Center': ('XL Center', 'Hartford', 'CT', 'arena', 100),
        'Hill Country BBQ': ('Hill Country Live', 'New York', 'NY', 'club', 100),
        'Hilton, Atlantic City': ('Hilton Atlantic City', 'Atlantic City', 'NJ', 'hotel', 100),
        'House of Blues (Vegas)': ('House of Blues', 'Las Vegas', 'NV', 'club', 100),
        'Ice Arena Tampa, FL': ('Amalie Arena', 'Tampa', 'FL', 'arena', 90),
        'Irish Pub of Cape Cod': ('Irish Pub', 'Cape Cod', 'MA', 'club', 100),
        'Irvington Town Hall': ('Irvington Theater', 'Irvington', 'NY', 'theater', 100),
        'Jones Beacj': ('Jones Beach Theater', 'Wantagh', 'NY', 'amphitheater', 100),
        'Klein Theater Bridgeport': ('Klein Memorial Auditorium', 'Bridgeport', 'CT', 'theater', 100),
        'Lincoln Financial': ('Lincoln Financial Field', 'Philadelphia', 'PA', 'stadium', 100),
        'Livin For You': ('Jones Beach Theater', 'Wantagh', 'NY', 'amphitheater', 100),
        'MSG Sphere (Vegas)': ('Sphere', 'Las Vegas', 'NV', 'arena', 100),
        'MSG Theather': ('The Theater at Madison Square Garden', 'New York', 'NY', 'theater', 100),
        'Manhattan Center': ('Hammerstein Ballroom', 'New York', 'NY', 'theater', 100),
        'Mayo Performing Arts': ('Mayo Performing Arts Center', 'Morristown', 'NJ', 'theater', 100),
        'Melody Tent': ('Cape Cod Melody Tent', 'Hyannis', 'MA', 'theater', 100),
        'Melrose Ballroom': ('Melrose Ballroom', 'Long Island City', 'NY', 'club', 100),
        'Mercury Lounge': ('Mercury Lounge', 'New York', 'NY', 'club', 100),
        'Metlife': ('MetLife Stadium', 'East Rutherford', 'NJ', 'stadium', 100),
        'Metroplitan Opera': ('Metropolitan Opera House', 'New York', 'NY', 'theater', 100),
        'Mid Hudson Civic Center': ('Mid-Hudson Civic Center', 'Poughkeepsie', 'NY', 'arena', 100),
        'Mill Hill Club': ('Mill Hill Club', 'West Yarmouth', 'MA', 'club', 100),
        'Minetta Lane': ('Minetta Lane Theatre', 'New York', 'NY', 'theater', 100),
        'Montage Mt, Scranton PA': ('Montage Mountain Amphitheater', 'Scranton', 'PA', 'amphitheater', 100),
        'Morristown Theater': ('Mayo Performing Arts Center', 'Morristown', 'NJ', 'theater', 90),
        'Mulcahey': ("Mulcahy's Pub", 'Wantagh', 'NY', 'club', 100),
        'NBC Plaza': ('Rockefeller Plaza', 'New York', 'NY', 'outdoor', 100),
        'Nasau': ('Nassau Coliseum', 'Uniondale', 'NY', 'arena', 100),
        'New Haven Coliseum': ('New Haven Coliseum', 'New Haven', 'CT', 'arena', 100),
        'Newark': ('Prudential Center', 'Newark', 'NJ', 'arena', 100),
        'Newark, NJ': ('Prudential Center', 'Newark', 'NJ', 'arena', 100),
        "O'Neill Center": ("O'Neill Theater Center", 'Waterford', 'CT', 'theater', 100),
        'OMaha (Qwest Center)': ('CHI Health Center', 'Omaha', 'NE', 'arena', 100),
        'OMaha Qwest Center': ('CHI Health Center', 'Omaha', 'NE', 'arena', 100),
        'Opry City Stage': ('Opry City Stage', 'New York', 'NY', 'club', 100),
        'Ossining Library': ('Ossining Public Library', 'Ossining', 'NY', 'theater', 100),
        'Outpost at Burbs': ('Outpost in the Burbs', 'Montclair', 'NJ', 'club', 100),
        'PNC Bank': ('PNC Park', 'Pittsburgh', 'PA', 'stadium', 100),
        'Palace Theatre Stamford': ('Palace Theatre', 'Stamford', 'CT', 'theater', 100),
        'Paramount': ('Paramount Theatre', 'Asbury Park', 'NJ', 'theater', 100),
        'Paramount Asbury (Rehearsal)': ('Paramount Theatre', 'Asbury Park', 'NJ', 'theater', 100),
        'Paramount Peekskill': ('Paramount Hudson Valley Theater', 'Peekskill', 'NY', 'theater', 100),
        'Patchogue Theatre': ('Patchogue Theatre', 'Patchogue', 'NY', 'theater', 100),
        'Phildelphia': ('Wells Fargo Center', 'Philadelphia', 'PA', 'arena', 90),
        'Pier 17': ('The Rooftop at Pier 17', 'New York', 'NY', 'outdoor', 100),
        'Pier A - Hoboken': ('Pier A Park', 'Hoboken', 'NJ', 'outdoor', 100),
        'Play Group Theatre': ('Play Group Theatre', 'White Plains', 'NY', 'theater', 100),
        'Playstatio Theater': ('Palladium Times Square', 'New York', 'NY', 'theater', 100),
        'Playstation Theater': ('Palladium Times Square', 'New York', 'NY', 'theater', 100),
        'Pleasantville Park': ('Pleasantville Park', 'Pleasantville', 'NY', 'outdoor', 100),
        'Portchester': ('Capitol Theatre', 'Port Chester', 'NY', 'theater', 100),
        'Portchster': ('Capitol Theatre', 'Port Chester', 'NY', 'theater', 100),
        'Purchase': ('SUNY Purchase', 'Purchase', 'NY', 'theater', 100),
        'QU': ('Quinnipiac University', 'Hamden', 'CT', 'arena', 100),
        'Queens College': ('Queens College', 'Queens', 'NY', 'theater', 100),
        'Radio City (Hillary)': ('Radio City Music Hall', 'New York', 'NY', 'theater', 100),
        "Randall's Island": ("Randall's Island Park", 'New York', 'NY', 'outdoor', 100),
        'Red Rocks': ('Red Rocks Amphitheatre', 'Morrison', 'CO', 'amphitheater', 100),
        'Ridgefiled Playhouse Field': ('Ridgefield Playhouse', 'Ridgefield', 'CT', 'theater', 100),
        'Riviera Chicago': ('Riviera Theatre', 'Chicago', 'IL', 'theater', 100),
        'Rockefeller Plaza': ('Rockefeller Plaza', 'New York', 'NY', 'outdoor', 100),
        'Rockin River Cruise': ('Rockin River Cruise', 'New York', 'NY', 'outdoor', 100),
        'Rumsey Playfield': ('Rumsey Playfield', 'New York', 'NY', 'outdoor', 100),
        'Saratoga': ('Saratoga Performing Arts Center', 'Saratoga Springs', 'NY', 'amphitheater', 100),
        'Schottenstein Center': ('Schottenstein Center', 'Columbus', 'OH', 'arena', 100),
        'Social Club': ('SubCulture', 'New York', 'NY', 'club', 100),
        'Southhampton College': ('Stony Brook Southampton', 'Southampton', 'NY', 'outdoor', 100),
        'Stage 48': ('Stage 48', 'New York', 'NY', 'club', 100),
        'Stamford Center': ('Stamford Center for the Arts', 'Stamford', 'CT', 'theater', 100),
        'Stamford Center for the Arts': ('Stamford Center for the Arts', 'Stamford', 'CT', 'theater', 100),
        'Stubbs BBQ': ("Stubb's Bar-B-Q", 'Austin', 'TX', 'club', 100),
        'Studio 6H': ('Studio 6H at 30 Rock', 'New York', 'NY', 'tv_studio', 100),
        'Tanner Park': ('Tanner Park', 'Copiague', 'NY', 'outdoor', 100),
        'Tappan Park': ('Tappan Park', 'Staten Island', 'NY', 'outdoor', 100),
        'Tarrytown': ('Tarrytown Music Hall', 'Tarrytown', 'NY', 'theater', 100),
        'The Metroplitan Opera': ('Metropolitan Opera House', 'New York', 'NY', 'theater', 100),
        'The Saint Asbury Park': (None, None, None, None, 0),  # User noted wrong date/venue
        'Times Square': ('Times Square', 'New York', 'NY', 'outdoor', 100),
        'Towne Crier Cafe': ('Towne Crier Cafe', 'Beacon', 'NY', 'club', 100),
        'Towne Criere': ('Towne Crier Cafe', 'Beacon', 'NY', 'club', 100),
        'Trump MArina, Atlantic City': ('Trump Marina', 'Atlantic City', 'NJ', 'casino', 100),
        'Turning Point': ('Turning Point', 'Piermont', 'NY', 'club', 100),
        'US Open Tennis Stadium': ('Arthur Ashe Stadium', 'Queens', 'NY', 'stadium', 100),
        'USA Upfront': ('USA Upfront', 'New York', 'NY', 'tv_studio', 90),
        'United Palace Theater': ('United Palace Theatre', 'New York', 'NY', 'theater', 100),
        'Universal Florida': ('Universal Studios Florida', 'Orlando', 'FL', 'outdoor', 100),
        'Verizon Center (NH)': ('SNHU Arena', 'Manchester', 'NH', 'arena', 100),
        'Wachovia Center': ('Wells Fargo Center', 'Philadelphia', 'PA', 'arena', 100),
        'Wall Street': ('Broad Street Ballroom', 'New York', 'NY', 'club', 100),
        'Webster': ('Webster Hall', 'New York', 'NY', 'club', 100),
        'Wester Bank Arena': ('Total Mortgage Arena', 'Bridgeport', 'CT', 'arena', 100),
        'Xfinity Hartford': ('Xfinity Theatre', 'Hartford', 'CT', 'amphitheater', 100),
        'Yonkers': ('Yonkers', 'Yonkers', 'NY', 'outdoor', 90),
        'Yorktown heights FDR Park': ('FDR State Park', 'Yorktown Heights', 'NY', 'outdoor', 100),
    }

    if original_name in mappings:
        return mappings[original_name]

    return (None, None, None, None, 0)

def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    input_file = project_root / "mappings" / "all_remaining_venues.csv"
    output_file = project_root / "mappings" / "all_remaining_venues_parsed.csv"

    # Read with proper encoding
    venues = []
    for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
        try:
            with open(input_file, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                venues = list(reader)
            print(f"Read file with encoding: {encoding}")
            break
        except UnicodeDecodeError:
            continue

    # Parse and update venues
    updated = 0
    skipped = 0

    for venue in venues:
        if venue['needs_review'] == 'YES':
            canonical, city, state, vtype, confidence = parse_venue_info(venue['original_name'], venue['notes'])

            if confidence >= 95 and canonical:
                venue['canonical_name'] = canonical
                venue['city'] = city
                venue['state'] = state
                venue['venue_type'] = vtype
                venue['needs_review'] = 'NO'
                updated += 1
                print(f"✓ {venue['original_name']:35s} → {city}, {state} ({vtype})")
            else:
                skipped += 1
                print(f"⊘ {venue['original_name']:35s} → SKIPPED (confidence: {confidence}%)")

    # Write output as UTF-8
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['original_name', 'canonical_name', 'city', 'state', 'venue_type', 'times_visited', 'needs_review', 'notes', 'NewNotes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(venues)

    print("\n" + "=" * 80)
    print(f"✓ Updated: {updated} venues")
    print(f"⊘ Skipped: {skipped} venues (need manual review)")
    print(f"\nOutput saved to: {output_file}")

if __name__ == "__main__":
    main()
