import argparse


def show_license_details():
    print(
        "This app is licensed under the GPL v3 or later license. Please see\n<https://www.gnu.org/licenses/gpl-3.0.en.html> for a complete copy of the license, as well as the LICENSE.md\nfile included with this Python package."
    )


def show_copying():
    print(
        "For full information on what is and is not allowed in term of copying, distribution, and\nreuse of the code in this app, please see the full license at\n<https://www.gnu.org/licenses/gpl-3.0.en.html>."
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--version",
        help="Show the version information for this app.",
        action="store_true",
    )
    parser.add_argument(
        "--license-details",
        help="Print the working license for this app.",
        action="store_true",
    )
    parser.add_argument(
        "--show-copying",
        help="Print the conditions under which the code for this app can be reused.",
        action="store_true",
    )
    args = parser.parse_args()
    if args.version:
        print("Mnemosyne Journaling by Siru: Version 0.1.0")
    elif args.license_details:
        show_license_details()
    elif args.show_copying:
        show_copying()
    else:
        pass
