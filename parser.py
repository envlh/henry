import re
import urllib.parse
import requests
import json


def normalize_lemma(lemma):
    return re.sub(r'[^a-z]', '', lemma)


def get_existing_lemmas(user_agent):
    url = 'https://query.wikidata.org/sparql?{}'.format(urllib.parse.urlencode({'query': 'SELECT DISTINCT ?lemma { [] wikibase:lemma ?lemma ; dct:language wd:Q12107 }', 'format': 'json'}))
    raw = requests.get(url, headers={'User-Agent': user_agent}).content
    res = json.loads(raw)['results']['bindings']
    existing_lemmas = []
    for value in res:
        existing_lemmas.append(normalize_lemma(value['lemma']['value']))
    return existing_lemmas


def load_json_file(filename):
    return json.loads(file_get_contents(filename))


def file_get_contents(filename):
    with open(filename, 'r', encoding='UTF-8') as f:
        s = f.read()
    return s


def build_lexeme(lemma, lexical_category, forms, dialects, page_number):
    lexeme = {'type': 'lexeme', 'language': 'Q25167', 'lemmas': {'br': {'language': 'br', 'value': lemma}}, 'lexicalCategory': lexical_category, 'forms': []}
    # forms + dialect / variety of form (P7481)
    for f in forms:
        claims = {}
        if len(dialects) >= 1:
            cl = []
            for dialect in dialects:
                cl.append({'mainsnak': {'snaktype': 'value', 'property': 'P7481', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': dialect[1:], 'id': dialect}, 'type': 'wikibase-entityid'}, 'datatype': 'wikibase-item'}, 'type': 'statement', 'rank': 'normal'})
            claims['P7481'] = cl
        form = {'representations': {'br': {'language': 'br', 'value': f}}, 'grammaticalFeatures': [], 'claims': claims}
        lexeme['forms'].append(form)
    # described by source (P1343)
    lexeme['claims'] = {
        'P1343': [{
            'mainsnak': {'snaktype': 'value', 'property': 'P1343', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 19216625, 'id': 'Q19216625'}, 'type': 'wikibase-entityid'}, 'datatype': 'wikibase-item'},
            'type': 'statement',
            'qualifiers': {
                'P304': [{'snaktype': 'value', 'property': 'P304', 'datavalue': {'value': page_number, 'type': 'string'}, 'datatype': 'string'}],
            },
            'qualifiers-order': ['P304'],
            'rank': 'normal'
        }]
    }
    return lexeme


def main():

    conf = load_json_file('conf/general.json')
    ref_lexical_categories = load_json_file('conf/lexical_categories.json')
    ref_dialects = load_json_file('conf/dialects.json')

    existing_lemmas = get_existing_lemmas(conf['user_agent'])

    content = file_get_contents('data/{}/stripped_{}.txt'.format(conf['iteration'], conf['iteration']))
    lines = content.split('\n')

    lexemes = []
    lexemes_error = []

    page_number = 1

    with open('data/{}/lexemes_{}.txt'.format(conf['iteration'], conf['iteration']), 'w', encoding='utf-8') as out:
        out.write('lemma,lexical_category,forms,dialects,page_number\n')

        for line in lines:

            line = line.strip()

            # line starting with a lemma (starting string surrounded by 3 single quotes)
            output = re.search(r'^\'\'\'(.*?)\'\'\'(.*)', line)
            if output is not None:

                # LEMMA and FORMS
                forms = output.group(1).strip().lower()
                # removing definition number
                forms = re.sub(r'^[0-9]+ ', '', forms)
                forms = forms.split(',')
                forms = [x.strip() for x in forms]
                # do not compute already existing lemmas
                lemma = forms[0]
                if normalize_lemma(lemma) in existing_lemmas:
                    lexemes_error.append({lemma: 'already existing in Wikidata'})
                    continue

                # DEFINITION
                definition = output.group(2)
                match = re.search(r'^( \([CLTV., ]+\))?, ([a-zéè\' .]+)', definition)
                if match is None:
                    lexemes_error.append({lemma: 'unable to parse definition'})
                    continue
                # DIALECTS
                dialects = match.group(1)
                if dialects is None:
                    dialects = []
                else:
                    dialects = re.findall(r'[CLTV]', dialects)
                    dialects = [ref_dialects[x] for x in dialects]

                # LEXICOGRAPHICAL CATEGORY
                parsed_lexical_category = match.group(2).strip()
                if parsed_lexical_category not in ref_lexical_categories:
                    lexemes_error.append({lemma: 'unknown lexical category ({})'.format(parsed_lexical_category)})
                    continue
                lexical_category = ref_lexical_categories[parsed_lexical_category]

                lexeme = build_lexeme(lemma, lexical_category, forms, dialects, page_number)
                out.write('{},{},{},{},{}\n'.format(lemma, lexical_category, forms, dialects, page_number))
                lexemes.append(lexeme)

            output = re.search(r'(?i)^{{nr\|', line)
            if output is not None:
                page_number += 1

    print('{} lexemes'.format(len(lexemes)))
    with open('data/{}/lexemes_{}.json'.format(conf['iteration'], conf['iteration']), 'w', encoding='utf-8') as myfile:
        myfile.write(json.dumps(lexemes))
    with open('data/{}/errors_{}.json'.format(conf['iteration'], conf['iteration']), 'w', encoding='utf-8') as myfile:
        myfile.write(json.dumps(lexemes_error))


if __name__ == '__main__':
    main()
