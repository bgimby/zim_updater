import os
import requests
from datetime import datetime
import datetime as dt
from collections import defaultdict
import xml.etree.ElementTree as ET
from torrentool.api import Torrent
import click

def load_current_lib() -> ET:
    """Load the kiwix zim library"""
    resp = requests.get("https://library.kiwix.org/catalog/root.xml")
    return ET.fromstring(resp.content)


def get_element_by_name(root: ET, name: str) -> ET:
    """Find an element given its name"""
    return root.findall("./{*}entry[{*}name='" + name + "']")


def print_element(e: ET):
    """Print an XML entry"""
    print(ET.tostring(e).decode("utf-8"))


def get_element_issued_date(e: ET) -> datetime:
    """Get an issued date for a zim XML entry"""
    issued_element = e.find("{*}issued")
    return datetime.strptime(issued_element.text.split("T")[0], "%Y-%m-%d")


def get_element_file_name(e: ET) -> str:
    """Get the file name for a zim XML entry"""
    link_element = e.find("{*}link[@type='text/html']")
    full_path = link_element.attrib["href"]
    return full_path.split("/")[-1]


def strip_date_from_file_name(name: str) -> str:
    """Generate the canonical zim name from a file name"""
    return "_".join(name.split("_")[:-1])


def get_element_by_file_name(root: ET, name: str) -> ET:
    """Search for a zim xml entry given a file name"""
    for entry in root.findall("./{*}entry"):
        if strip_date_from_file_name(
            get_element_file_name(entry)
        ) == strip_date_from_file_name(name):
            return entry


def torrent_link_for_element(e: ET) -> str:
    """Get the torrent link for a zim xml entry"""
    link = e.find("{*}link[@type='application/x-zim']").attrib["href"]
    return link.replace(".meta4", ".torrent")


def get_file_name_issued_date(name: str) -> datetime:
    """Get the issued date for a zim file from its filename"""
    return datetime.strptime(name.split("_")[-1], "%Y-%m")


def element_newer_than_file(name: str, element: ET) -> bool:
    """Check if a zim xml entry is newer than another zim file"""
    file_date = get_file_name_issued_date(name)
    element_date = get_element_issued_date(element)
    # filenames only record the month while elements include the day
    # this could be off if the element was generated early in a month
    # and the file is less than a month old during a short month
    return element_date - file_date > dt.timedelta(days=31)


def get_updated_elements(root: ET, name_list: list[str]) -> list[ET]:
    """Get updated zims from xml list given current filenames"""
    elements = []
    # might be better to construct a dict here to avoid n^2
    for name in name_list:
        entry = get_element_by_file_name(root, name)
        if entry is None:
            print(f"Can't find entry for file {name}")
            continue
        if element_newer_than_file(name, entry):
            elements.append(entry)

    return elements


def get_torrents_from_elements(elements: list[ET]) -> dict[str, str]:
    """Returns a dict from file name to torrent link"""
    return {
        strip_date_from_file_name(get_element_file_name(e)): torrent_link_for_element(e)
        for e in elements
    }


def load_old_file_names() -> list[str]:
    """Load a list of file names from 'all_zims'"""
    f = open("all_zims", "r")
    return eval(f.read())


def download_torrents(torrent_list: str, torrent_path: str) -> None:
    """Download a list of torrent links to the given path"""
    for url in torrent_list:
        filename = torrent_path + url.split("/")[-1]
        print(f"Downloading {filename}")
        try:
            r = requests.get(url, allow_redirects=True)
        except Exception as e:
            print(f"Error downloading {url}:", e)
            continue
        f = open(filename, "wb")
        f.write(r.content)
        print(f"Verifying {filename}")
        try:
            t = Torrent.from_file(filename)
        except Exception as e:
            print("Error verifying torrentfile:", e)
            continue


def find_updates(path: str) -> dict[str, str]:
    """get map from zim name to torrentfiles for all updated zims in path"""
    try:
        root = load_current_lib()
        zims = list_zims_in_path(path)
        stripped_date_map = {strip_date_from_file_name(z): z for z in zims}
        updated_elements = get_updated_elements(root, zims)
        if len(updated_elements):
            print("Will download torrents for:")
        for element in updated_elements:
            new_name = get_element_file_name(element)
            canonical_name = strip_date_from_file_name(new_name)
            old_name = stripped_date_map[canonical_name]
            new_date = new_name.split("_")[-1]
            old_date = old_name.split("_")[-1]
            print(f"    {canonical_name}: {old_date} -> {new_date}")
        torrents = get_torrents_from_elements(updated_elements)
        return torrents
    except Exception as e:
        print("Error finding updated zims")
        raise e


def list_zims_in_path(p: str) -> list[str]:
    """Get .zim files in path and return their names"""
    files = [f for f in os.listdir(p) if os.path.isfile(p + "/" + f)]
    zims = [f[:-4] for f in files if f.endswith(".zim")]
    return zims


def list_old_zims(zims: list[str]) -> dict[str, dict[str, str]]:
    """Generate map of canonical names to matching files"""
    stripped_map = defaultdict(list)
    olds = {}
    for zim in zims:
        stripped_map[strip_date_from_file_name(zim)].append(zim)

    for name, matches in stripped_map.items():
        if len(matches) > 1:
            keep, *old = sorted(
                matches, key=lambda name: get_file_name_issued_date(name), reverse=True
            )
            olds[name] = {"keep": keep, "old": old}
    return olds


@click.group()
def cli():
    """CLI tool for updating zims via kiwix.org

    This tool allows checking for updated versions of zims from kiwix.org,
    downloading new zims, and removing old versions of zims.
    """
    pass


@cli.command(
    short_help="Download torrentfiles for zims in path with newer versions available",
    no_args_is_help=True,
)
@click.option("--assume-yes", "-y", is_flag=True, help="Assume yes to all questions")
@click.option(
    "--zim-path",
    default=".",
    help="Path containing zim files to update",
    show_default=True,
)
@click.option(
    "--torrent-path",
    default="./torrent",
    help="Path to download new torrentfiles to",
    show_default=True,
)
def update(assume_yes: bool, zim_path: str, torrent_path: str) -> None:
    """Download torrentfiles for zims in path with newer versions available

    Reads through the given directory for any zim files, downloads the current
    library list from kiwix.org, and checks for any new zims that match
    those in the directory. If there are any, it downloads torrentfiles for
    them to the provided path.

    This assumes zims end with `_YYYY-MM.zim`, which is the standard for the
    kiwix library.
    """
    torrent_list = list(find_updates(zim_path).values())
    if len(torrent_list):
        if not assume_yes:
            i = input(
                f"Download torrentfiles for {len(torrent_list)} new zims? (y/N): "
            )
            if i.lower() == "y":
                assume_yes = True
        if assume_yes:
            download_torrents(torrent_list, torrent_path)
    else:
        print("No newer versions of zims found")


@cli.command(
    short_help="Delete old duplicate zims in a directory", no_args_is_help=True
)
@click.option("--assume-yes", "-y", is_flag=True, help="Assume yes to all questions")
@click.option("--path", default=".", help="Path containing zim files to clean")
def clean(assume_yes: bool, path: str) -> None:
    """Delete old duplicate zims in a directory

    Reads through the given directory for any zim files, and removes old zims
    that have the same name as newer ones.

    This assumes zims end with `_YYYY-MM.zim`, which is the standard for the
    kiwix library.
    """
    zims = list_zims_in_path(path)
    old_map = list_old_zims(zims)
    to_delete = []
    for name, status in old_map.items():
        print(f"Found duplicate for {name}")
        print(f"  Will keep: {status['keep']}")
        print(f"  Will remove: {status['old']}")
        to_delete.extend([n + ".zim" for n in status["old"]])
    if len(to_delete):
        if not assume_yes:
            i = input("Delete {len(to_delete)} old zims? (y/N): ")
            if i.lower() == "y":
                assume_yes = True
        if assume_yes:
            for name in to_delete:
                print(f"Deleting {name}")
                os.remove(path + "/" + name)
    else:
        print("No duplicate zims found")


if __name__ == "__main__":
    cli()
