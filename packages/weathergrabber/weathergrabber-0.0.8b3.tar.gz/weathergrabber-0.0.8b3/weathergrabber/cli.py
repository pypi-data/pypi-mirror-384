import argparse
import os
import weathergrabber

def main_cli():
    ## Get current locale, or use the default one
    parser = argparse.ArgumentParser(description="Weather forecast grabber from weather.com")
    parser.add_argument("location_name", type=str, nargs='?', help="Location (city name, zip code, etc.)")
    parser.add_argument("--location-id", "-l", type=str, help="64-character-hex code for location obtained from weather.com")
    parser.add_argument("--lang", "-L", type=str, help="Language (pt-BR, fr-FR, etc.), If not set, uses the machine one.")
    parser.add_argument("--output", "-o", type=str, choices=['console','json','waybar'], default='console', help="Output format. console, json or waybar")
    parser.add_argument("--keep-open", "-k",action='store_true', default=False, help="Keep open and refreshing every 5 minutes instead of exiting after execution. Does only makes sense for --output=console")
    parser.add_argument("--icons", "-i", type=str, choices=['fa','emoji'], default='emoji', help="Icon set. 'fa' for Font-Awesome, or 'emoji'")
    parser.add_argument("--version", "-v", action='version', version=f'Weathergrabber {weathergrabber.get_version()}', help="Show version and exit")
    parser.add_argument(
        "--log",
        default="critical",
        choices=["debug", "info", "warning", "error", "critical", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: CRITICAL)"
    )
    args = parser.parse_args()

    # Check for language and location from environment variables if not provided as arguments
    lang = args.lang if args.lang else os.getenv("LANG","en_US.UTF-8").split(".")[0].replace("_","-")
    location_id = args.location_id 
    if not args.location_id and not args.location_name:
        location_id = os.getenv('WEATHER_LOCATION_ID')

    weathergrabber.main(
        log_level=args.log,
        location_name = args.location_name,
        location_id = location_id,
        lang=lang,
        output=args.output,
        keep_open=args.keep_open,
        icons=args.icons
    )

if __name__ == "__main__":
    main_cli()
