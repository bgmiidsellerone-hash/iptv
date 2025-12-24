import datetime as dt
import requests
import xml.etree.ElementTree as ET

# Target timezone: Asia/Kolkata (UTC+5:30)
IST_OFFSET = dt.timedelta(hours=5, minutes=30)

# Your channels mapped to epg.pw IDs
CHANNELS = {
    "disneychannel": 464229,
    "hungama": 463988,
    "sonysabhd": 463827,
    "sethd": 464105,
    "sonysab": 463922,
    "sonyten3hd": 464048,
    "sonypal": 463919,
    "starsports1hd": 464249,
    "starsports2hd": 463839,
    "sonyyay": 464116,
}

# Per-channel source timezone offsets (relative to UTC)
# Moscow: UTC+3, Paris: UTC+1, Kolkata: UTC+5:30
CHANNEL_SOURCE_OFFSETS = {
    "disneychannel": dt.timedelta(hours=3),             # Moscow
    "hungama": IST_OFFSET,                              # Kolkata
    "sonysabhd": dt.timedelta(hours=1),                 # Paris
    "sethd": IST_OFFSET,                                # Kolkata
    "sonysab": IST_OFFSET,                              # Kolkata
    "sonyten3hd": IST_OFFSET,                           # Kolkata
    "sonypal": dt.timedelta(hours=3),                   # Moscow
    "starsports1hd": IST_OFFSET,                        # Kolkata
    "starsports2hd": IST_OFFSET,                        # Kolkata
    "sonyyay": IST_OFFSET,                              # Kolkata
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
    channels_def = {
        "disneychannel": "Disney Channel",
        "hungama": "Hungama",
        "sonysabhd": "Sony SAB HD",
        "sethd": "SET HD",
        "sonysab": "Sony SAB",
        "sonyten3hd": "Sony TEN 3 HD",
        "sonypal": "Sony PAL",
        "starsports1hd": "Star Sports 1 Hindi HD",
        "starsports2hd": "Star Sports 2 Hindi HD",
        "sonyyay": "Sony Yay",
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

def parse_xmltv_time(value: str) -> dt.datetime:
    """
    Parse XMLTV time like '20251223003000 +0000'
    into an aware datetime in UTC.
    """
    value = value.strip()
    # split base time and offset
    if " " in value:
        base, offset = value.split(" ", 1)
    else:
        base, offset = value, "+0000"

    # parse base (YYYYMMDDHHMMSS)
    dt_base = dt.datetime.strptime(base, "%Y%m%d%H%M%S")

    # parse offset like +0530 or -0200
    sign = 1 if offset[0] == "+" else -1
    hours = int(offset[1:3])
    minutes = int(offset[3:5])
    delta = dt.timedelta(hours=hours, minutes=minutes) * sign

    # return as UTC
    return dt_base - delta

def format_xmltv_time_ist(utc_dt: dt.datetime) -> str:
    """
    Take a UTC datetime and return XMLTV string in IST (+0530).
    """
    ist_dt = utc_dt + IST_OFFSET
    return ist_dt.strftime("%Y%m%d%H%M%S") + " +0530"

def normalize_programme_times(prog: ET.Element, source_offset: dt.timedelta):
    """
    Convert programme start/stop from source_offset to IST.
    If the XML already has an offset, we try to respect it; but we mainly
    rely on the per-channel source_offset.
    """
    for attr in ["start", "stop"]:
        v = prog.get(attr)
        if not v:
            continue

        # Parse existing value assuming its offset is the one epg.pw used
        # (we ignore the original offset and instead use source_offset)
        value = v.strip()
        if " " in value:
            base, _ = value.split(" ", 1)
        else:
            base = value

        # build naive datetime from base
        dt_base = dt.datetime.strptime(base, "%Y%m%d%H%M%S")

        # interpret as local for source channel, then to UTC
        utc_dt = dt_base - source_offset

        # format to IST
        prog.set(attr, format_xmltv_time_ist(utc_dt))

def copy_programmes(epg_root, target_channel_id):
    source_offset = CHANNEL_SOURCE_OFFSETS.get(target_channel_id, IST_OFFSET)
    for prog in epg_root.findall("programme"):
        prog.set("channel", target_channel_id)
        normalize_programme_times(prog, source_offset)
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
