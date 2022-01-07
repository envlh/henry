import json
import os.path
import parser
import pywikibot
import random


def create_lexeme(site, lexeme):
    request = {
        "action": "wbeditentity",
        "format": "json",
        "new": "lexeme",
        "summary": "[[:d:Wikidata:Requests for permissions/Bot/EnvlhBot 1|Henry import]]",
        "token": site.tokens['edit'],
        "data": lexeme,
    }
    site._simple_request(**request).submit()


def get_site():
    site = pywikibot.Site('wikidata', 'wikidata')
    site.login()
    return site


def main():
    conf = parser.load_json_file('conf/general.json')
    todo_filepath = 'data/lexemes_todo.json'
    if os.path.isfile(todo_filepath):
        lexemes = parser.load_json_file(todo_filepath)
    else:
        lexemes = parser.load_json_file('data/{}/lexemes_{}.json'.format(conf['iteration'], conf['iteration']))
    lexeme = json.dumps(lexemes.pop(random.randrange(len(lexemes))))
    with open(todo_filepath, 'w', encoding='utf-8') as myfile:
        json.dump(lexemes, myfile, ensure_ascii=False)
    print(lexeme)
    site = get_site()
    create_lexeme(site, lexeme)


if __name__ == '__main__':
    main()
