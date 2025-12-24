import datetime as dt
import requests
import xml.etree.ElementTree as ET

# Target timezone: Asia/Kolkata (UTC+5:30)
IST_OFFSET = dt.timedelta(hours=5, minutes=30)

# Your channels mapped to epg.pw IDs (order matters in Python 3.7+)
CHANNELS = {
    "hungama": 463988,
    "disneychannel": 464229,
    "sonyyay": 464116,
    "sonypal": 463919,
    "sonysab": 463922,
    "sonysabhd": 463827,
    "sethd": 464105,
    "starsports1hd": 464249,
    "starsports2hd": 463839,
    "sonyten3hd": 464048,
}

BASE_URL = "https://epg.pw/api/epg.xml?lang=en&date={date}&channel_id={cid}"

tv = ET.Element(
    "tv",
    {
        "generator-info-name": "Custom Merged EPG",
        "source-info-name": "epg.pw",
        "source-info-url": "https://epg.pw/xmltv.html?lang=en",
    },
)

def add_channels():
    # Same order here so <channel> elements follow your sequence
    channels_def = {
        "hungama": "Hungama",
        "disneychannel": "Disney Channel",
        "sonyyay": "Sony Yay",
        "sonypal": "Sony PAL",
        "sonysab": "Sony SAB",
        "sonysabhd": "Sony SAB HD",
        "sethd": "SET HD",
        "starsports1hd": "Star Sports 1 Hindi HD",
        "starsports2hd": "Star Sports 2 Hindi HD",
        "sonyten3hd": "Sony TEN 3 HD",
    }
    for cid, name in channels_def.items():
        ch = ET.SubElement(tv, "channel", {"id": cid})
        dn = ET.SubElement(ch, "display-name")
        dn.text = name

def fetch_epg(date_str, epg_id):
    url = BASE_URL.format(date=date_str, cid=epg_id)
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return ET.fromstring(r.content)

def normalize_programme_times_to_ist(prog: ET.Element):
    """
    Treat source times as Kolkata local and force +0530 offset.
    """
    for attr in ["start", "stop"]:
        v = prog.get(attr)
        if not v:
            continue

        value = v.strip()
        if " " in value:
            base, _ = value.split(" ", 1)
        else:
            base = value

        dt_base = dt.datetime.strptime(base, "%Y%m%d%H%M%S")
        prog.set(attr, dt_base.strftime("%Y%m%d%H%M%S") + " +0530")

def copy_programmes(epg_root, target_channel_id):
    for prog in epg_root.findall("programme"):
        prog.set("channel", target_channel_id)
        normalize_programme_times_to_ist(prog)
        tv.append(prog)

def main():
    add_channels()

    today = dt.date.today()
    dates = [today, today + dt.timedelta(days=1)]
    date_strs = [d.strftime("%Y%m%d") for d in dates]

    for xmltv_id, epg_id in CHANNELS.items():
        for d in date_strs:
            try:
                epg_root = fetch_epg(d, epg_id)
                copy_programmes(epg_root, xmltv_id)
            except Exception as e:
                print(f"Error for {xmltv_id} {d}: {e}")

    tree = ET.ElementTree(tv)
    tree.write("epg.xml", encoding="UTF-8", xml_declaration=True)

if __name__ == "__main__":
    main()
