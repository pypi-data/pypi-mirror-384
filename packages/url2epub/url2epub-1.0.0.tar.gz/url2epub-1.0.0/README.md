# url2epub

A CLI program to convert an URL to an epub using Readability & Pandoc.

Uses:

- _Readability_ : Removes all the menu/footers/header you don't want to read anyway.
- _Pandoc_ : Converts to `epub`/`epub3` formats.
- _Request_ : Retrieve webpage.

## installation

Needs the following python packages:

```
readability-lxml
pandoc
requests
```

you can either get them from your package manager, or from `pip`.

```shell
pip install -r requirement.txt
```

## usage

```shell
#EXAMPLE
url2epub.py myverygoodwebsite.com/article

url2epub.py --help
#usage: url2epub.py --url myverygoodwebsite.com/article --outfile /mnt/my-ereader/article.epub
#
#Downloads a webpage, extracts the readable content using Readability, and saves it to an epub to be read on your favorite e-reader using Pandoc.
#
#positional arguments:
#  URL                   URL to get the epub from. If not present, 'http://' will be prepended to the argument.
#
#options:
#  -h, --help            show this help message and exit
#  -o, --outfile OUTFILE
#                        Outfile to save the ebook to. If not present, will try to make up a name from the webpage's title. Might overwrite existing file, use with caution.
#  --epub3               Saves the book in epub3 format (default=False)
```
