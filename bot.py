import json

import pywikibot


def build_lexeme(lexical_category, lemma):
    return json.dumps({"type": "lexeme", "language": "Q25167", "lexicalCategory": lexical_category, "lemmas": {'br': {"language": "br", "value": lemma}}})


def create_lexeme(site, lexeme):
    request = {
        "action": "wbeditentity",
        "format": "json",
        "new": "lexeme",
        "summary": "test for [[:d:Wikidata:Requests for permissions/Bot/EnvlhBot 1]]",
        "token": site.tokens['edit'],
        "data": lexeme,
    }
    print(request)
    site._simple_request(**request).submit()


def get_site():
    site = pywikibot.Site('test', 'wikidata')
    site.login()
    return site


def main():
    lexeme = build_lexeme("Q1084", "adreûz")
    site = get_site()
    create_lexeme(site, lexeme)


if __name__ == '__main__':
    main()
