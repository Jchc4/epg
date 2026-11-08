#!/usr/bin/env python3
"""
Consolidated Sports EPG Merger
Combines UK, Ireland, US Sports, Peacock, Australia, New Zealand, DStv SuperSport,
and beIN Sports English into a single, compact epg.xml.gz.
Tailored 100% to the exact tvg-ids and channel names in the user's playlist,
guaranteeing seamless, deterministic matching without guessing or fallbacks.
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
    ("US_MAJOR", "https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz", None),
    ("PEACOCK", "https://epgshare01.online/epgshare01/epg_ripper_PEACOCK1.xml.gz", None),
    ("AU", "https://epgshare01.online/epgshare01/epg_ripper_AU1.xml.gz", None),
    ("NZ", "https://epgshare01.online/epgshare01/epg_ripper_NZ1.xml.gz", None),
    ("SUPERSPORT", "https://i.mjh.nz/DStv/za.xml.gz", lambda cid, dn: cid.startswith('2') and ('ss ' in dn.lower() or 'supersport' in dn.lower() or 'espn' in dn.lower())),
    ("BEIN", "https://epgshare01.online/epgshare01/epg_ripper_BEIN1.xml.gz", None),
]

DIRECT_ID_MAP = {
    # Sky Sports UK
    'SkySportsMainEvent.uk': 'SkySpMainEvHD.uk',
    'SkySportsPremiereLeague.uk': 'SkySp.PL.HD.uk',
    'Sky.Sports.Football.HD.uk': 'SkySp.Fball.HD.uk',
    'Sky.Sports.NFL.uk': 'Sky.Sports.NFL.uk',
    'SkySportsArena.uk': 'SkySportsArena.uk',
    'SkySportsCricket.uk': 'SkySpCricket.HD.uk',
    'SkySportsGolf.uk': 'SkySp.Golf.HD.uk',
    'SkySportsMix.uk': 'SkySp.Mix.HD.uk',
    'SkySportsNews.uk': 'SkySp.News.HD.uk',
    'SkySportsRacing.uk': 'SkySp.Racing.HD.uk',
    'SkySportsTennis.uk': 'SkySp.Tennis.HD.uk',
    'SkySportsF1.uk': 'SkySp.F1.HD.uk',
    'RacingUK.uk': 'RacingUK.uk',

    # TNT Sports UK
    'TNTSport1.uk': 'TNT.Sports.1.HD.uk',
    'TNTSport2.uk': 'TNT.Sports.2.HD.uk',
    'TNTSport3.uk': 'TNT.Sports.3.HD.uk',
    'TNTSport4.uk': 'TNT.Sports.4.HD.uk',
    'TNTUltimate.uk': 'TNT.Sports.Ultimate.HD.uk',
    'BTSport4ESPN.uk': 'BTSport4ESPN.uk',

    # Premier Sports & Viaplay
    'ViaplaySports1.uk': 'Premier.Sports.1.HD.uk',
    'ViaplaySports2.uk': 'Premier.Sports.2.HD.uk',

    # Irish Channels
    'RTEOne.ie': 'RTE.One.HD.ie',
    'RTETwo.ie': 'RTE.Two.HD.ie',
    'TG4.ie': 'TG4.HD.ie',
    'VirginMediaOne.ie': 'Virgin.Media.One.HD.ie',
    'VirginMediaTwo.ie': 'Virgin.Media.Two.HD.ie',
    'VirginMediaThree.ie': 'Virgin.Media.Three.HD.ie',
    'RTEJr.ie': 'RTE.KIDSjr.ie',
    'RTENewsNow.ie': 'RTE.News.Now.ie',

    # New Zealand
    'SkySport1.nz': 'Sky.Sport.1.nz',
    'SkySport2.nz': 'Sky.Sport.2.nz',
    'SkySport3.nz': 'Sky.Sport.3.nz',
    'SkySport4.nz': 'Sky.Sport.4.nz',
    'SkySport5.nz': 'Sky.Sport.5.nz',
    'SkySport6.nz': 'Sky.Sport.6.nz',
    'SkySport7.nz': 'Sky.Sport.7.nz',
    'SkySport8.nz': 'Sky.Sport.8.nz',
    'SkySport9.nz': 'Sky.Sport.9.nz',

    # beIN Sports
    'beINSports1En.qa': 'beIN.Sports.1.English.bein',
    'beINSports2En.qa': 'beIN.Sports.2.English.bein',
    'beINSports3En.qa': 'beIN.Sports.3.English.bein',
    'beINSportsNews.qa': 'beINSportsNews.qa',
    'BeinSports1EnEn.qa': 'beIN.Sports.1.English.bein',
    'BeinSports2EnEn.qa': 'beIN.Sports.2.English.bein',
    'BeinSports3EnEn.qa': 'beIN.Sports.3.English.bein',

    # US Major Networks
    'US-Fox Sports 1': 'FS1.Fox.Sports.1.HD.us2',
    'US-Fox Sports 2': 'FS2.HD.us2',
    'ESPN.us': 'ESPN.HD.us2',
    'ESPN2.us': 'ESPN2.HD.us2',
    'ESPNU.us': 'ESPNU.HD.us2',
    'US-ESPN News': 'ESPNEWS.HD.us2',
    'US-CBS Sports Network USA': 'CBS.Sports.Network.HD.us2',
    'US-NBC Sports Boston': 'NBC.Sports.Boston.HD.us2',
    'US-NBC Sports Philadelphia': 'NBC.Sports.Philadelphia.HD.us2',
    'US-NBC Sports California': 'NBC.Sports.California.SAT.us2',
    'US-NFL Network': 'NFL.Network.HD.us2',
    'US-NFL Red Zone': 'NFL.RedZone.HD.us2',
    'US-MLB Network': 'MLB.Network.HD.us2',
    'US-NBA TV USA': 'NBA.TV.HD.us2',
    'US-NHL Network USA': 'NHL.Network.HD.us2',
    'US| NBC GOLF': 'Golf.Channel.HD.us2',
    'US| TNT HD': 'TNT.HD.us2',
    'US| TNT WEST HD': 'TNT.HD.us2',
    'US| YES NETWORK HD': 'YES.Network.HD.us2',
    'PokerGo.us': 'PokerGO.HD.us2',
    'WWE.us': 'WWE.HD.us2',

    # Australian Channels
    'beINSports1.au': 'beINSports1.au',
    'beINSports2.au': 'beINSports2.au',
    'beINSports3.au': 'beINSports3.au',
    'FoxSportsNews.au': 'FoxSportsNews.au',
    'FoxSports3.au': 'FoxSports503.au',
}

NAME_TO_FEED_ID = {
    'UK - SKY SPORTS MAIN EVENTS UHD': 'SkySpMainEvHD.uk',
    'UK - SKY SPORTS ACTION FHD': 'SkySp.ActionHD.uk',
    'UK - SKY SPORTS DARTS UHD': 'SkySpMainEvHD.uk',
    'UK - SKY SPORTS DARTS FHD': 'SkySpMainEvHD.uk',
    'UK - SKY SPORTS DARTS': 'SkySpMainEvHD.uk',
    'UK - PREMIER SPORT LALIGA TV UHD': 'Premier.Sports.1.HD.uk',
    'UK - PREMIER SPORT LALIGA TV FHD': 'Premier.Sports.1.HD.uk',
    'UK - MUTV': 'MUTV.uk',
    'UK - MAN UNITED FHD': 'MUTV.uk',
    'UK - CELTIC TV': 'CelticTV.uk',
    'UK - RANGERS TV LIVE EVENT': 'RangersTV.uk',

    # SuperSport channels
    'UK - SUPERSPORT PL UHD': '203.dstv_com',
    'UK - SUPERSPORT PL HD': '203.dstv_com',
    'UK - SUPERSPORT FOOTBALL UHD': '205.dstv_com',
    'UK - SUPERSPORT FOOTBALL HD': '205.dstv_com',
    'UK - SUPERSPORT GRANDSTAND UHD': '201.dstv_com',
    'UK - SUPERSPORT GRANDSTAND HD': '201.dstv_com',
    'UK - SUPERSPORT PSL UHD': '202.dstv_com',
    'UK - SUPERSPORT PSL HD': '202.dstv_com',
    'UK - SUPERSPORT LIGA UHD': '204.dstv_com',
    'UK - SUPERSPORT LIGA HD': '204.dstv_com',
    'UK - SUPERSPORT ACTION UHD': '209.dstv_com',
    'UK - SUPERSPORT ACTION HD': '209.dstv_com',
    'UK - SUPERSPORT CRICKET UHD': '212.dstv_com',
    'UK - SUPERSPORT CRICKET HD': '212.dstv_com',
    'UK - SUPERSPORT GOLF UHD': '213.dstv_com',
    'UK - SUPERSPORT GOLF HD': '213.dstv_com',
    'UK - SUPERSPORT TENNIS UHD': '214.dstv_com',
    'UK - SUPERSPORT TENNIS HD': '214.dstv_com',
    'UK - SUPERSPORT MOTORSPORT UHD': '215.dstv_com',
    'UK - SUPERSPORT MOTORSPORT HD': '215.dstv_com',
    'UK - SUPERSPORT RUGBY UHD': '211.dstv_com',
    'UK - SUPERSPORT RUGBY HD': '211.dstv_com',
    'UK - SUPERSPORT BLITZ UHD': '200.dstv_com',
    'UK - SUPERSPORT BLITZ HD': '200.dstv_com',
    'UK - SUPERSPORT MAXIMO UHD': '241.dstv_com',
    'UK - SUPERSPORT MAXIMO HD': '241.dstv_com',
    'UK - SUPER SPORT PLAY 1 UHD': '203.dstv_com',
    'UK - SUPERSPORT PLAY 2 UHD': '205.dstv_com',
    'UK - SUPERSPORT VARIETY 1 UHD': '209.dstv_com',
    'UK - SUPERSPORT VARIETY 2 UHD': '209.dstv_com',
    'UK - SUPERSPORT VARIETY 3 UHD': '209.dstv_com',
    'UK - SUPERSPORT VARIETY 4 UHD': '209.dstv_com',

    # Ireland channels
    'IE - RTE ONE FHD': 'RTE.One.HD.ie',
    'IE - RTE TWO UHD': 'RTE.Two.HD.ie',
    'IE - TG4': 'TG4.HD.ie',
    'IE - TG 4 UHD': 'TG4.HD.ie',
    'IE - VIRGIN MEDIA ONE': 'Virgin.Media.One.HD.ie',
    'IE - VIRGIN MEDIA TWO': 'Virgin.Media.Two.HD.ie',
    'IE - VIRGIN MEDIA THREE': 'Virgin.Media.Three.HD.ie',
    'IE - VIRGIN MEDIA FOUR': 'Virgin.Media.Four.HD.ie',
    'IE - VM 1 FHD': 'Virgin.Media.One.HD.ie',
    'IE - VM 2 FHD': 'Virgin.Media.Two.HD.ie',
    'IE - VM 3 FHD': 'Virgin.Media.Three.HD.ie',
}

OUTPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "epg.xml.gz"

def main():
    print(f"Starting merge of {len(FEEDS)} feeds into {OUTPUT_FILE}...")
    
    feed_channels = {}
    feed_programmes = {}
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
            feed_cids = set()
            for ch in root.findall('channel'):
                cid = ch.get('id')
                if not cid or cid in feed_channels:
                    continue
                dn_text = ch.find('display-name').text if ch.find('display-name') is not None else ''
                if filter_fn and not filter_fn(cid, dn_text):
                    continue

                feed_channels[cid] = ch
                feed_cids.add(cid)
                count_ch += 1

            count_pr = 0
            for pr in root.findall('programme'):
                cid = pr.get('channel')
                if cid in feed_cids:
                    feed_programmes.setdefault(cid, []).append(pr)
                    count_pr += 1

            print(f"  -> Added {count_ch} channels and {count_pr} programmes from {name}")
        except Exception as e:
            print(f"  [!] Warning: Failed {name}: {e}")

    output_channels_xml = []
    output_programmes_xml = []
    emitted_channel_ids = set()

    # 1. Base channels
    for cid, ch_el in feed_channels.items():
        emitted_channel_ids.add(cid)
        output_channels_xml.append(ET.tostring(ch_el, encoding='utf-8').decode('utf-8'))
        for pr_el in feed_programmes.get(cid, []):
            output_programmes_xml.append(ET.tostring(pr_el, encoding='utf-8').decode('utf-8'))

    # 2. Injected tvg-ids
    for tid, source_cid in DIRECT_ID_MAP.items():
        if tid in emitted_channel_ids or source_cid not in feed_channels:
            continue
        source_ch = feed_channels[source_cid]
        new_ch = ET.Element('channel', id=tid)
        d0 = ET.SubElement(new_ch, 'display-name')
        d0.text = tid
        for dn in source_ch.findall('display-name'):
            d = ET.SubElement(new_ch, 'display-name')
            d.text = dn.text
        
        output_channels_xml.append(ET.tostring(new_ch, encoding='utf-8').decode('utf-8'))
        emitted_channel_ids.add(tid)

        for pr in feed_programmes.get(source_cid, []):
            pr_clone = ET.fromstring(ET.tostring(pr, encoding='utf-8'))
            pr_clone.set('channel', tid)
            output_programmes_xml.append(ET.tostring(pr_clone, encoding='utf-8').decode('utf-8'))

    # 3. Injected exact names
    for ch_name, source_cid in NAME_TO_FEED_ID.items():
        if ch_name in emitted_channel_ids or source_cid not in feed_channels:
            continue
        source_ch = feed_channels[source_cid]
        new_ch = ET.Element('channel', id=ch_name)
        d0 = ET.SubElement(new_ch, 'display-name')
        d0.text = ch_name
        for dn in source_ch.findall('display-name'):
            d = ET.SubElement(new_ch, 'display-name')
            d.text = dn.text

        output_channels_xml.append(ET.tostring(new_ch, encoding='utf-8').decode('utf-8'))
        emitted_channel_ids.add(ch_name)

        for pr in feed_programmes.get(source_cid, []):
            pr_clone = ET.fromstring(ET.tostring(pr, encoding='utf-8'))
            pr_clone.set('channel', ch_name)
            output_programmes_xml.append(ET.tostring(pr_clone, encoding='utf-8').decode('utf-8'))

    print(f"\nWriting combined EPG with {len(output_channels_xml)} channels and {len(output_programmes_xml)} programmes...")
    with gzip.open(OUTPUT_FILE, 'wt', encoding='utf-8') as out:
        out.write('<?xml version="1.0" encoding="utf-8"?>\n')
        out.write('<tv generator-info-name="JCTV-Sports-EPG">\n')
        for ch_str in output_channels_xml:
            out.write(ch_str)
        for pr_str in output_programmes_xml:
            out.write(pr_str)
        out.write('</tv>\n')

    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"Done! Created {OUTPUT_FILE} ({size_mb:.2f} MB)")

if __name__ == '__main__':
    main()
