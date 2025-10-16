# Author : berru@riseup.net
# Source : https://git.sr.ht/~berru/url2epub

import pandoc
import requests
import argparse
import re
import string
import random
from readability import Document
from sys import exit


def random_alphanum(size: int) -> str:
    return "".join(
        random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
        for _ in range(16)
    )


def sanitize_name(page_title: str) -> str:
    sane_name = re.sub(r"[^a-z0-9\-_]+", "", page_title.replace(" ", "_").lower())
    if len(sane_name) == 0:
        sane_name = random_alphanum(8)
    return f"{sane_name}.epub"


def main():
    parser = argparse.ArgumentParser(
        prog="url2epub",
        usage="url2epub.py --url myverygoodwebsite.com/article --outfile /mnt/my-ereader/article.epub",
        description="Downloads a webpage, extracts the readable content using Readability, and saves it to an epub to be read on your favorite e-reader using Pandoc.",
    )
    parser.add_argument(
        metavar="URL",
        dest="url",
        help="URL to get the epub from. If not present, 'http://' will be prepended to the argument.",
    )
    parser.add_argument(
        "-o",
        "--outfile",
        type=argparse.FileType("w"),
        help="Outfile to save the ebook to. If not present, will try to make up a name from the webpage's title. Might overwrite existing file, use with caution.",
    )
    parser.add_argument(
        "--epub3",
        action="store_true",
        default=False,
        help="Saves the book in epub3 format (default=False)",
    )

    options = parser.parse_args()
    url = options.url if options.url.startswith("http") else f"http://{options.url}"

    response = requests.get(url)
    if response.status_code != 200:
        exit(-1)
    else:
        document = Document(response.text)
        outfile_path = (
            options.outfile.name
            if options.outfile
            else sanitize_name(document.short_title())
        )
        pandoc.write(
            pandoc.read(source=document.summary(), format="HTML"),
            file=outfile_path,
            format="epub3" if options.epub3 else "epub",
        )
        print(f"Saved to '{outfile_path}'")


if __name__ == "__main__":
    main()
