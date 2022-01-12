import json
import os.path
import parser
import pywikibot
import random


def create_lexeme(site, lexeme):
    request = {
        'action': 'wbeditentity',
        'format': 'json',
        'new': 'lexeme',
        'summary': '[[:d:Wikidata:Requests for permissions/Bot/EnvlhBot 1|Henry import]]',
        'token': site.tokens['edit'],
        'bot': '1',
        'data': lexeme,
    }
    site._simple_request(**request).submit()


def get_site():
    site = pywikibot.Site('wikidata', 'wikidata')
    site.login()
    return site


def main():
    conf = parser.load_json_file('conf/general.json')
    site = get_site()
    todo_filepath = 'data/lexemes_todo.json'
    done = parser.load_json_file(conf['done_filepath'])
    if os.path.isfile(todo_filepath):
        lexemes = parser.load_json_file(todo_filepath)
    else:
        lexemes = parser.load_json_file('data/{}/lexemes_{}.json'.format(conf['iteration'], conf['iteration']))
    for i in range(0, 100):
        if len(lexemes) < 1:
            break
        lexeme = lexemes.pop(random.randrange(len(lexemes)))
        lexeme_str = json.dumps(lexeme, ensure_ascii=False)
        print(lexeme_str)
        done.append(lexeme['lemmas']['br']['value'])
        with open(conf['done_filepath'], 'w', encoding='utf-8') as myfile:
            json.dump(done, myfile, ensure_ascii=False)
        with open(todo_filepath, 'w', encoding='utf-8') as myfile:
            json.dump(lexemes, myfile, ensure_ascii=False)
        create_lexeme(site, lexeme_str)


if __name__ == '__main__':
    main()
