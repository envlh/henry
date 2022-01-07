# Description

Scripts to import the dictionary [_Lexique étymologique du breton moderne_](https://fr.wikisource.org/wiki/Livre:Henry_-_Lexique_%C3%A9tymologique_du_breton_moderne.djvu) [Q19216625](https://www.wikidata.org/wiki/Q19216625) by Victor Henry ([Q1386172](https://www.wikidata.org/wiki/Q1386172)) from Wikisource to Wikidata's lexicographical data. This dictionary is in French about the Breton language.

# Requirements

* PHP 7.3+
* Python 3.7+

# Installation

Example on Debian-like system:

    apt install php php-curl python3 python3-pip

    pip3 install -r requirements.txt

# Usage

## Crawler

Retrieves content from Wikisource, aggregates all pages in one file, and does some cleaning.

    php -f crawler.php

Several files are generated:
* `wikitext.txt`: raw wikitext crawled from Wikisource (useful for debug)
* `stripped.txt`: wikitext after cleaning

## Parser

Parses previously created file and converts it into machine-readable format.

    python3 parser.py

Several files are generated:
* `lexemes.json`: lexemes that will be imported in Wikidata, serialized in Wikibase JSON format
* `lexemes.txt`: more human-readable list of lexemes that will be imported
* `errors.json`: rejected lexemes, with reason of error
* `monograms.json` and `bigrams.json`: frequencies of letters in lemmas

## Import

Imports the data in Wikidata's lexicographical data.

    python3 bot.py

# Copyright

This project, mainly by [Envel Le Hir](https://www.lehir.net/) (@envlh) for the code and Nicolas Vigneron (@belett) for the Wikisource transcription, is under [CC0](https://creativecommons.org/publicdomain/zero/1.0/) license (public domain dedication).
