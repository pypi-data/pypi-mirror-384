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

recommended installation is via `pipx`

```shell
pipx install url2epub
```

## usage

Download a page (filename auto-determined from title page)

```shell
url2epub.py myverygoodwebsite.com/article
```

Download a page to a specific filename

```shell
url2epub.py myverygoodwebsite.com/article --outfile my_file.epub
```

Save to epub3 format

```shell
url2epub.py myverygoodwebsite.com/article --epub3
```
