import requests, re
from datetime import datetime, timedelta

CHANNELS = {
    "disneychannel": "464229",
    "hungama": "463988",
    "sonysabhd": "463827",
    "sethd": "464105",
    "sonysab": "463922",
    "sonyten3hd": "464048",
    "sonypal": "463919",
    "starsports1hd": "464249",
    "starsports2hd": "463839",
}

programmes = []

for day in range(2):  # 48 hours
    date = (datetime.now() + timedelta(days=day)).strftime("%Y%m%d")

    for channel, cid in CHANNELS.items():
        url = f"https://epg.pw/api/epg.xml?lang=en&date={date}&channel_id={cid}"
        xml = requests.get(url, timeout=20).text

        for p in re.findall(r"<programme.*?</programme>", xml, re.S):
            p = re.sub(r'channel="[^"]+"', f'channel="{channel}"', p)
            programmes.append(p)

with open("epg.xml", "r", encoding="utf-8") as f:
    base = f.read().split("</tv>")[0]

with open("epg.xml", "w", encoding="utf-8") as f:
    f.write(base + "\n" + "\n".join(programmes) + "\n</tv>")
