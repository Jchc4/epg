#!/usr/bin/env python3
"""
Merges the 6 sports XMLTV feeds (UK, US, AU, NZ, ZA, BEIN) into a single,
compact epg.xml.gz file.
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
