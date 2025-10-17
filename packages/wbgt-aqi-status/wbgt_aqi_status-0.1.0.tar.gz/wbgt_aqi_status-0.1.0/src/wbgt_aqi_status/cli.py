import argparse, json, sys
from .core import get_status, Thresholds

def main():
    p = argparse.ArgumentParser(description="Heat Index + AQI → practice status (OK/Modify/Cancel)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--zip", help="US ZIP code, e.g., 33774")
    g.add_argument("--lat", type=float, help="Latitude (e.g., 27.909)")
    p.add_argument("--lon", type=float, help="Longitude (e.g., -82.787)")
    p.add_argument("--tz", default="America/New_York", help="IANA timezone (default America/New_York)")
    p.add_argument("--time", dest="when", help='Local time "HH:MM" to check (default: current hour)')
    p.add_argument("--hi-amber", type=int, default=95)
    p.add_argument("--hi-red", type=int, default=103)
    p.add_argument("--aqi-amber", type=int, default=101)
    p.add_argument("--aqi-red", type=int, default=151)
    p.add_argument("--json", action="store_true", help="Output JSON")
    args = p.parse_args()

    if args.lat is not None and args.lon is None:
        p.error("--lat requires --lon")

    th = Thresholds(args.hi_amber, args.hi_red, args.aqi_amber, args.aqi_red)
    try:
        s = get_status(zip_code=args.zip, lat=args.lat, lon=args.lon, tz=args.tz, when=args.when, thresholds=th)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(s, ensure_ascii=False))
    else:
        print(f"{s['status']} — HI={s['heat_index_f']}°F; AQI={s['aqi_us']}  ({s['timestamp']})")
