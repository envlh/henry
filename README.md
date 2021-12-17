# Description

Scripts to import [_Lexique étymologique du breton moderne_](https://fr.wikisource.org/wiki/Livre:Henry_-_Lexique_%C3%A9tymologique_du_breton_moderne.djvu) from Wikisource to Wikidata's lexicographical data.

# Usage

## Crawler

Retrieves content from Wikisource, does some cleaning and aggregates all pages in one file.

    php -f crawler.php

## Parser

Parses previously created file and convert into machine-readable format.

    python parser.py

## Import

Imports the data in Wikidata's lexicographical data.

    python bot.py

# Copyright

This project, mainly by [Envel Le Hir](https://www.lehir.net/) (@envlh) for the code and Nicolas Vigneron (@belett) for the Wikisource transcription, is under [CC0](https://creativecommons.org/publicdomain/zero/1.0/) license (public domain dedication).
