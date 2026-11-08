#!/usr/bin/env python3
"""
Consolidated Sports EPG Merger
Combines UK, Ireland, US Sports, Peacock, Australia, New Zealand, DStv SuperSport,
and beIN Sports English into a single, compact epg.xml.gz.
Includes comprehensive display-name aliases so auto-matchers never mislink channels.
"""
import gzip
import io
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

FEEDS = [
    ("UK", "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz", None),
    ("IE", "https://epgshare01.online/epgshare01/epg_ripper_IE1.xml.gz", None),
    ("US_MAJOR", "https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz",
     lambda cid, dn: any(k in dn.lower() or k in cid.lower() for k in [
         'espn', 'fs1', 'fs2', 'fox sports', 'nbc sports', 'usa network', 'cbs sports',
         'golf channel', 'tennis channel', 'mlb network', 'nfl network', 'nba tv', 'nhl network',
         'tnt', 'tbs', 'tru tv'
     ])),
    ("PEACOCK", "https://epgshare01.online/epgshare01/epg_ripper_PEACOCK1.xml.gz", None),
    ("AU", "https://epgshare01.online/epgshare01/epg_ripper_AU1.xml.gz",
     lambda cid, dn: any(k in dn.lower() or k in cid.lower() for k in ['sport', 'espn', 'bein'])),
    ("NZ", "https://epgshare01.online/epgshare01/epg_ripper_NZ1.xml.gz", None),
    ("SUPERSPORT", "https://i.mjh.nz/DStv/za.xml.gz",
     lambda cid, dn: cid.startswith('2') and ('ss ' in dn.lower() or 'supersport' in dn.lower() or 'espn' in dn.lower())),
    ("BEIN", "https://epgshare01.online/epgshare01/epg_ripper_BEIN1.xml.gz", None),
]

NAME_ALIASES = {
    # UK Sky Sports
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
    "SkySp.Fball.uk": ["Sky Sports Football", "Sky Sports Football SD"],
    "SkySp.F1.HD.uk": [
        "Sky Sports F1", "Sky Sports Formula 1", "Sky Sports F1 HD", "Sky Sports F1 FHD", "Sky Sports F1 UHD"
    ],
    "SkySp.F1.uk": ["Sky Sports F1", "Sky Sports Formula 1"],
    "SkySpCricket.HD.uk": [
        "Sky Sports Cricket", "Sky Sports Cricket HD", "Sky Sports Cricket FHD", "Sky Sports Cricket UHD"
    ],
    "SkySp.Cricket.uk": ["Sky Sports Cricket"],
    "SkySp.Golf.HD.uk": [
        "Sky Sports Golf", "Sky Sports Golf HD", "Sky Sports Golf FHD", "Sky Sports Golf UHD"
    ],
    "SkySp.Golf.uk": ["Sky Sports Golf"],
    "SkySp.ActionHD.uk": [
        "Sky Sports Action", "Sky Sports Action HD", "Sky Sports Action FHD", "Sky Sports Action UHD"
    ],
    "SkySp.Action.uk": ["Sky Sports Action"],
    "SkySportsArena.uk": [
        "Sky Sports Arena", "Sky Sports Arena HD", "Sky Sports Arena FHD", "Sky Sports Arena UHD"
    ],
    "SkySp.News.HD.uk": [
        "Sky Sports News", "Sky Sports News HD", "Sky Sports News FHD", "Sky Sports News UHD"
    ],
    "SkySp.Racing.HD.uk": [
        "Sky Sports Racing", "Sky Sports Racing HD", "Sky Sports Racing FHD", "Sky Sports Racing UHD"
    ],
    "SkySp.Racing.uk": ["Sky Sports Racing"],
    "SkySp.Mix.HD.uk": ["Sky Sports Mix", "Sky Sports Mix HD", "Sky Sports Mix FHD"],
    "SkySp.Tennis.HD.uk": [
        "Sky Sports Tennis", "Sky Sports Tennis HD", "Sky Sports Tennis FHD", "Sky Sports Tennis UHD"
    ],
    "SkySp+HD.uk": ["Sky Sports+", "Sky Sports+ HD", "Sky Sports Plus", "Sky Sports+ FHD"],
    "SkySp+.uk": ["Sky Sports+", "Sky Sports Plus"],
    "Sky.Sports.NFL.uk": ["Sky Sports NFL", "Sky Sports NFL HD", "Sky Sports NFL FHD", "Sky Sports NFL UHD"],
    "Sky.Sports.Ultra.HD.1.uk": ["Sky Sports Ultra HD 1", "Sky Sports UHD 1"],
    "Sky.Sports.Ultra.HD.2.uk": ["Sky Sports Ultra HD 2", "Sky Sports UHD 2"],

    # UK TNT Sports
    "TNT.Sports.1.HD.uk": ["TNT Sports 1", "TNT Sports 1 HD", "TNT Sports 1 FHD", "TNT Sports 1 UHD"],
    "TNT.Sports.2.HD.uk": ["TNT Sports 2", "TNT Sports 2 HD", "TNT Sports 2 FHD", "TNT Sports 2 UHD"],
    "TNT.Sports.3.HD.uk": ["TNT Sports 3", "TNT Sports 3 HD", "TNT Sports 3 FHD", "TNT Sports 3 UHD"],
    "TNT.Sports.4.HD.uk": ["TNT Sports 4", "TNT Sports 4 HD", "TNT Sports 4 FHD", "TNT Sports 4 UHD"],
    "TNT.Sports.Ultimate.HD.uk": ["TNT Sports Ultimate", "TNT Sport Ultimate", "TNT Sports Ultimate HD", "TNT Sports Ultimate UHD"],
    "BTSport4ESPN.uk": ["TNT Sports ESPN", "TNT Sports ESPN HD", "TNT Sports ESPN UHD", "BT Sport ESPN"],

    # UK Premier Sports & Viaplay
    "Premier.Sports.1.HD.uk": ["Premier Sports 1", "Premier Sports 1 HD", "Premier Sports 1 FHD", "Premier Sports 1 UHD"],
    "Premier.Sports.2.HD.uk": ["Premier Sports 2", "Premier Sports 2 HD", "Premier Sports 2 FHD", "Premier Sports 2 UHD"],

    # Ireland
    "RTE.One.HD.ie": ["RTE One", "RTE One HD", "RTE ONE FHD", "RTE 1"],
    "RTE.Two.HD.ie": ["RTE Two", "RTE Two HD", "RTE TWO FHD", "RTE TWO UHD", "RTE 2"],
    "TG4.HD.ie": ["TG4", "TG4 HD", "TG 4 UHD"],
    "Virgin.Media.One.HD.ie": ["Virgin Media One", "Virgin Media One HD", "VM 1 FHD"],
    "Virgin.Media.Two.HD.ie": ["Virgin Media Two", "Virgin Media Two HD", "VM 2 FHD"],
    "Virgin.Media.Three.HD.ie": ["Virgin Media Three", "Virgin Media Three HD", "VM 3 FHD"],
    "Virgin.Media.Four.HD.ie": ["Virgin Media Four", "Virgin Media Four HD"],

    # DStv SuperSport
    "200.dstv_com": ["SuperSport Blitz", "SuperSport Blitz HD", "SuperSport Blitz UHD", "SS Blitz"],
    "201.dstv_com": ["SuperSport Grandstand", "SuperSport Grandstand HD", "SuperSport Grandstand UHD", "SS Grandstand"],
    "202.dstv_com": ["SuperSport PSL", "SuperSport PSL HD", "SuperSport PSL UHD", "SS PSL"],
    "203.dstv_com": ["SuperSport Premier League", "SuperSport PL", "SuperSport PL HD", "SuperSport PL UHD", "SS Premier League"],
    "204.dstv_com": ["SuperSport La Liga", "SuperSport Liga", "SuperSport Liga UHD", "SS La Liga"],
    "205.dstv_com": ["SuperSport Football", "SuperSport Football HD", "SuperSport Football UHD", "SS Football"],
    "209.dstv_com": ["SuperSport Action", "SuperSport Action HD", "SuperSport Action UHD", "SS Action"],
    "211.dstv_com": ["SuperSport Rugby", "SuperSport Rugby HD", "SuperSport Rugby UHD", "SS Rugby"],
    "212.dstv_com": ["SuperSport Cricket", "SuperSport Cricket HD", "SuperSport Cricket UHD", "SS Cricket"],
    "213.dstv_com": ["SuperSport Golf", "SuperSport Golf HD", "SuperSport Golf UHD", "SS Golf"],
    "214.dstv_com": ["SuperSport Tennis", "SuperSport Tennis HD", "SuperSport Tennis UHD", "SS Tennis"],
    "215.dstv_com": ["SuperSport Motorsport", "SuperSport Motorsport HD", "SuperSport Motorsport UHD", "SS MotorSport"],
    "241.dstv_com": ["SuperSport Maximo", "SuperSport Maximo HD", "SuperSport Maximo UHD", "SS Maximo"],

    # US Major
    "FS1.Fox.Sports.1.HD.us2": ["Fox Sports 1", "FS1", "FS1 HD", "Fox Sports 1 HD"],
    "FS1.HD.us2": ["Fox Sports 1", "FS1", "FS1 HD"],
    "ESPN.HD.us2": ["ESPN", "ESPN HD"],
    "ESPN2.HD.us2": ["ESPN2", "ESPN2 HD"],
    "ESPNEWS.HD.us2": ["ESPNews", "ESPNEWS HD"],
    "ESPNU.HD.us2": ["ESPNU", "ESPNU HD"],
    "USA.Network.HD.us2": ["USA Network", "USA Network HD"],
    "CBS.Sports.Network.HD.us2": ["CBS Sports Network", "CBS Sports Network HD"],
    "CBS.Sports.Golazo.Network.us2": ["CBS Sports Golazo", "CBS Sports Golazo Network"],
    "NBC.Sports.Now.us2": ["NBC Sports Now", "NBC Sports"],
    "[PK22].NBC.Sports.NOW.PEACOCK": ["Peacock NBCSports", "Peacock PremierLeague", "NBC Sports NOW"],
}

OUTPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "epg.xml.gz"

def main():
    print(f"Starting merge of {len(FEEDS)} feeds into {OUTPUT_FILE}...")
    seen_channel_ids = set()
    channels_xml = []
    programmes_xml = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for name, url, filter_fn in FEEDS:
        print(f"Fetching {name} from {url}...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=90) as resp:
                compressed_data = resp.read()
            with gzip.GzipFile(fileobj=io.BytesIO(compressed_data)) as gz:
                tree = ET.parse(gz)
                root = tree.getroot()

            count_ch = 0
            feed_ch_ids = set()
            for ch in root.findall('channel'):
                ch_id = ch.get('id')
                if not ch_id or ch_id in seen_channel_ids:
                    continue
                dn_text = ch.find('display-name').text if ch.find('display-name') is not None else ''
                if filter_fn and not filter_fn(ch_id, dn_text):
                    continue

                seen_channel_ids.add(ch_id)
                feed_ch_ids.add(ch_id)

                if ch_id in NAME_ALIASES:
                    existing_names = {dn.text for dn in ch.findall('display-name') if dn.text}
                    for alias in reversed(NAME_ALIASES[ch_id]):
                        if alias not in existing_names:
                            dn_el = ET.Element('display-name')
                            dn_el.text = alias
                            ch.insert(0, dn_el)

                channels_xml.append(ET.tostring(ch, encoding='utf-8').decode('utf-8'))
                count_ch += 1

            count_pr = 0
            for pr in root.findall('programme'):
                ch_id = pr.get('channel')
                if ch_id in feed_ch_ids:
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
