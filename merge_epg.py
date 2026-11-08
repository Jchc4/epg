#!/usr/bin/env python3
"""
Merges the 6 sports XMLTV feeds (UK, US, AU, NZ, ZA, BEIN) into a single,
compact epg.xml.gz file, with comprehensive display-name aliases so auto-matchers
(in JCTV, m3u4u, etc.) accurately match channels without greedy fallbacks.
"""
import gzip
import io
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

FEEDS = [
    ("UK", "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz"),
    ("US", "https://epgshare01.online/epgshare01/epg_ripper_US_SPORTS1.xml.gz"),
    ("AU", "https://epgshare01.online/epgshare01/epg_ripper_AU1.xml.gz"),
    ("NZ", "https://epgshare01.online/epgshare01/epg_ripper_NZ1.xml.gz"),
    ("ZA", "https://epgshare01.online/epgshare01/epg_ripper_ZA1.xml.gz"),
    ("BEIN", "https://epgshare01.online/epgshare01/epg_ripper_BEIN1.xml.gz"),
]

# Raw UK EPG abbreviates Sky Sports as 'SkySp' which causes auto-matchers
# to latch onto the only fully-spelled channel: Sky Sports NFL.
# Adding standard full names & common IPTV aliases fixes auto-matching everywhere.
NAME_ALIASES = {
    "SkySpMainEvHD.uk": [
        "Sky Sports Main Event", "Sky Sports Main Event HD", "Sky Sports Main Event FHD",
        "Sky Sports Main Events", "Sky Sports Main Events UHD", "Sky Sports Main Event UHD"
    ],
    "SkySp.PL.HD.uk": [
        "Sky Sports Premier League", "Sky Sports PL", "Sky Sports PL HD",
        "Sky Sports PL FHD", "Sky Sports PL UHD", "Sky Sports Premier League HD"
    ],
    "SkySp.Fball.HD.uk": [
        "Sky Sports Football", "Sky Sports Football HD", "Sky Sports Football FHD", "Sky Sports Football UHD"
    ],
    "SkySp.Fball.uk": [
        "Sky Sports Football", "Sky Sports Football SD"
    ],
    "SkySp.F1.HD.uk": [
        "Sky Sports F1", "Sky Sports Formula 1", "Sky Sports F1 HD", "Sky Sports F1 FHD", "Sky Sports F1 UHD"
    ],
    "SkySp.F1.uk": [
        "Sky Sports F1", "Sky Sports Formula 1"
    ],
    "SkySpCricket.HD.uk": [
        "Sky Sports Cricket", "Sky Sports Cricket HD", "Sky Sports Cricket FHD", "Sky Sports Cricket UHD"
    ],
    "SkySp.Cricket.uk": [
        "Sky Sports Cricket"
    ],
    "SkySp.Golf.HD.uk": [
        "Sky Sports Golf", "Sky Sports Golf HD", "Sky Sports Golf FHD", "Sky Sports Golf UHD"
    ],
    "SkySp.Golf.uk": [
        "Sky Sports Golf"
    ],
    "SkySp.ActionHD.uk": [
        "Sky Sports Action", "Sky Sports Action HD", "Sky Sports Action FHD", "Sky Sports Action UHD"
    ],
    "SkySp.Action.uk": [
        "Sky Sports Action"
    ],
    "SkySp.News.HD.uk": [
        "Sky Sports News", "Sky Sports News HD", "Sky Sports News FHD", "Sky Sports News UHD"
    ],
    "SkySp.Racing.HD.uk": [
        "Sky Sports Racing", "Sky Sports Racing HD", "Sky Sports Racing FHD", "Sky Sports Racing UHD"
    ],
    "SkySp.Racing.uk": [
        "Sky Sports Racing"
    ],
    "SkySp.Mix.HD.uk": [
        "Sky Sports Mix", "Sky Sports Mix HD", "Sky Sports Mix FHD"
    ],
    "SkySp.Tennis.HD.uk": [
        "Sky Sports Tennis", "Sky Sports Tennis HD", "Sky Sports Tennis FHD", "Sky Sports Tennis UHD"
    ],
    "SkySp+HD.uk": [
        "Sky Sports+", "Sky Sports+ HD", "Sky Sports Plus", "Sky Sports+ FHD"
    ],
    "SkySp+.uk": [
        "Sky Sports+", "Sky Sports Plus"
    ],
    "TNT.Sports.1.HD.uk": [
        "TNT Sports 1", "TNT Sports 1 HD", "TNT Sports 1 FHD", "TNT Sports 1 UHD"
    ],
    "TNT.Sports.2.HD.uk": [
        "TNT Sports 2", "TNT Sports 2 HD", "TNT Sports 2 FHD", "TNT Sports 2 UHD"
    ],
    "TNT.Sports.3.HD.uk": [
        "TNT Sports 3", "TNT Sports 3 HD", "TNT Sports 3 FHD", "TNT Sports 3 UHD"
    ],
    "TNT.Sports.4.HD.uk": [
        "TNT Sports 4", "TNT Sports 4 HD", "TNT Sports 4 FHD", "TNT Sports 4 UHD"
    ],
    "TNT.Sports.Ultimate.HD.uk": [
        "TNT Sports Ultimate", "TNT Sport Ultimate", "TNT Sports Ultimate HD", "TNT Sports Ultimate UHD"
    ],
}

OUTPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "epg.xml.gz"

def main():
    print(f"Starting merge of {len(FEEDS)} feeds into {OUTPUT_FILE}...")
    
    seen_channel_ids = set()
    channels_xml = []
    programmes_xml = []

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for name, url in FEEDS:
        print(f"Fetching {name} from {url}...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                compressed_data = resp.read()
            
            with gzip.GzipFile(fileobj=io.BytesIO(compressed_data)) as gz:
                tree = ET.parse(gz)
                root = tree.getroot()

            count_ch = 0
            for ch in root.findall('channel'):
                ch_id = ch.get('id')
                if ch_id and ch_id not in seen_channel_ids:
                    seen_channel_ids.add(ch_id)
                    
                    # Add aliases if this channel has known abbreviation issues
                    if ch_id in NAME_ALIASES:
                        existing_names = {dn.text for dn in ch.findall('display-name') if dn.text}
                        for alias in NAME_ALIASES[ch_id]:
                            if alias not in existing_names:
                                dn_el = ET.Element('display-name')
                                dn_el.text = alias
                                ch.insert(0, dn_el)
                    
                    channels_xml.append(ET.tostring(ch, encoding='utf-8').decode('utf-8'))
                    count_ch += 1

            count_pr = 0
            for pr in root.findall('programme'):
                ch_id = pr.get('channel')
                if ch_id in seen_channel_ids:
                    programmes_xml.append(ET.tostring(pr, encoding='utf-8').decode('utf-8'))
                    count_pr += 1

            print(f"  -> Added {count_ch} channels and {count_pr} programmes from {name}")

        except Exception as e:
            print(f"  [!] Warning: Failed to fetch {name}: {e}")

    print(f"\nWriting combined EPG with {len(channels_xml)} channels and {len(programmes_xml)} programmes...")
    with gzip.open(OUTPUT_FILE, 'wt', encoding='utf-8') as out:
        out.write('<?xml version="1.0" encoding="utf-8"?>\n')
        out.write('<tv generator-info-name="JCTV-Sports-EPG">\n')
        for ch_str in channels_xml:
            out.write(ch_str)
        for pr_str in programmes_xml:
            out.write(pr_str)
        out.write('</tv>\n')

    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"Done! Created {OUTPUT_FILE} ({size_mb:.2f} MB)")

if __name__ == '__main__':
    main()
