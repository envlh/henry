import json
import re
import requests
import unidecode
import urllib.parse


def normalize_lemma(lemma):
    return re.sub(r'[^a-z]', '', unidecode.unidecode(lemma))


def get_existing_entries(user_agent):
    url = 'https://query.wikidata.org/sparql?{}'.format(urllib.parse.urlencode({'query': 'SELECT DISTINCT (REPLACE(?statedAs, "’", "\'") AS ?statedAs) { ?lexeme p:P1343 [ ps:P1343 wd:Q19216625 ; pq:P1932 ?statedAs ] . }', 'format': 'json'}))
    raw = requests.get(url, headers={'User-Agent': user_agent}).content
    res = json.loads(raw)['results']['bindings']
    existing_entries = []
    for value in res:
        existing_entries.append(value['statedAs']['value'])
    return existing_entries


def load_json_file(filename):
    return json.loads(file_get_contents(filename))


def file_get_contents(filename):
    with open(filename, 'r', encoding='UTF-8') as f:
        s = f.read()
    return s


def build_lexeme(lemma, lexical_category, gender, number, forms, dialects, page_number, stated_as):
    lexeme = {'type': 'lexeme', 'language': 'Q12107', 'lemmas': {'br': {'language': 'br', 'value': lemma}}, 'lexicalCategory': lexical_category, 'forms': []}
    # forms + dialect / variety of form (P7481)
    for f in forms:
        claims = {}
        if len(dialects) >= 1:
            cl = []
            for dialect in dialects:
                cl.append({'mainsnak': {'snaktype': 'value', 'property': 'P7481', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': dialect[1:], 'id': dialect}, 'type': 'wikibase-entityid'}, 'datatype': 'wikibase-item'}, 'type': 'statement', 'rank': 'normal'})
            claims['P7481'] = cl
        form = {'representations': {'br': {'language': 'br', 'value': f}}, 'grammaticalFeatures': [], 'claims': claims, 'add': ''}
        # positive for adjectives
        if lexical_category == 'Q34698':
            form['grammaticalFeatures'] = ['Q3482678']
        # infinitive for verbs
        elif lexical_category == 'Q24905':
            form['grammaticalFeatures'] = ['Q179230']
        # number for nouns
        elif lexical_category == 'Q1084' and number is not None:
            form['grammaticalFeatures'] = [number]
        lexeme['forms'].append(form)
    # described by source (P1343)
    first_letter = normalize_lemma(lemma)[:1]
    if lemma[:3] == 'c\'h':
        first_letter = 'c\'h'
    elif lemma[:2] == 'ch':
        first_letter = 'ch'
    first_letter = first_letter.upper()
    lexeme['claims'] = {
        'P1343': [{
            'mainsnak': {'snaktype': 'value', 'property': 'P1343', 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 19216625, 'id': 'Q19216625'}, 'type': 'wikibase-entityid'}, 'datatype': 'wikibase-item'},
            'type': 'statement',
            'qualifiers': {
                'P304': [{'snaktype': 'value', 'property': 'P304', 'datavalue': {'value': str(page_number), 'type': 'string'}, 'datatype': 'string'}],
                'P953': [{'snaktype': 'value', 'property': 'P953', 'datavalue': {'value': 'https://fr.wikisource.org/wiki/Lexique_%C3%A9tymologique_du_breton_moderne/{}#{}'.format(first_letter, page_number), 'type': 'string'}, 'datatype': 'url'}],
                "P1932": [{'snaktype': 'value', 'property': 'P1932', 'datavalue': {'value': stated_as, 'type': 'string'}, 'datatype': 'string'}],
            },
            'qualifiers-order': ['P304', 'P953', 'P1932'],
            'rank': 'normal'
        }]
    }
    # gender (P5185)
    if gender is not None:
        lexeme['claims']['P5185'] = [{'mainsnak': {'snaktype': 'value', 'property': 'P5185', 'datavalue': {'value': {'entity-type': "item", 'numeric-id': int(gender[1:]), 'id': gender}, "type": "wikibase-entityid"}, "datatype": "wikibase-item"}, "type": "statement", "rank": "normal"}]
    # reconstructed word (P31)
    if lemma[0] == '*':
        lexeme['claims']['P31'] = [{'mainsnak': {'snaktype': 'value', "'property": "P31", 'datavalue': {'value': {'entity-type': 'item', 'numeric-id': 55074511, 'id': 'Q55074511'}, 'type': 'wikibase-entityid'}, 'datatype': 'wikibase-item'}, 'type': 'statement', 'rank': 'normal'}]
    return lexeme


def main():

    conf = load_json_file('conf/general.json')
    ref_lexical_categories = load_json_file('conf/lexical_categories.json')
    ref_genders = load_json_file('conf/genders.json')
    ref_numbers = load_json_file('conf/numbers.json')
    ref_dialects = load_json_file('conf/dialects.json')

    # already existing
    existing_entries = get_existing_entries(conf['user_agent'])

    content = file_get_contents('data/{}/stripped_{}.txt'.format(conf['iteration'], conf['iteration']))
    lines = content.split('\n')

    lexemes = []
    lexemes_error = []
    monograms = {}
    bigrams = {}

    page_number = 1

    with open('data/{}/lexemes_{}.txt'.format(conf['iteration'], conf['iteration']), 'w', encoding='utf-8') as out:
        out.write('lemma,lexical_category,gender,number,forms,dialects,page_number\n')

        for line in lines:

            line = line.strip()

            # line starting with a lemma (starting string surrounded by 3 single quotes)
            output = re.search(r'^\'\'\'(.*?)\'\'\'(.*)', line)
            if output is not None:

                # STATED AS (entry label)
                stated_as = output.group(1).strip()
                if stated_as in existing_entries:
                    lexemes_error.append({lemma: 'entry "{}" already used in Wikidata'.format(stated_as)})
                    continue

                # LEMMA and FORMS
                # removing definition number
                forms = re.sub(r'^[0-9]+ ', '', stated_as.lower())
                forms = forms.split(',')
                forms = [x.strip() for x in forms]
                # do not compute already existing lemmas
                lemma = forms[0]

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

                # GENDER
                gender = None
                if parsed_lexical_category in ref_genders:
                    gender = ref_genders[parsed_lexical_category]

                # NUMBER
                number = None
                if parsed_lexical_category in ref_numbers:
                    number = ref_numbers[parsed_lexical_category]

                lexeme = build_lexeme(lemma, lexical_category, gender, number, forms, dialects, page_number, stated_as)
                lexemes.append(lexeme)

                out.write('{},{},{},{},{},{},{}\n'.format(lemma, lexical_category, gender, number, forms, dialects, page_number))

                for c in lemma:
                    if c not in monograms:
                        monograms[c] = 0
                    monograms[c] += 1
                for (a, b) in zip(lemma[0::2], lemma[1::2]):
                    if (a + b) not in bigrams:
                        bigrams[a + b] = 0
                    bigrams[a + b] += 1

            output = re.search(r'(?i)^{{nr\|', line)
            if output is not None:
                page_number += 1

    with open('data/{}/lexemes_{}.json'.format(conf['iteration'], conf['iteration']), 'w', encoding='utf-8') as myfile:
        json.dump(lexemes, myfile, ensure_ascii=False)
    with open('data/{}/errors_{}.json'.format(conf['iteration'], conf['iteration']), 'w', encoding='utf-8') as myfile:
        json.dump(lexemes_error, myfile, ensure_ascii=False)
    with open('data/{}/monograms_{}.json'.format(conf['iteration'], conf['iteration']), 'w', encoding='utf-8') as myfile:
        json.dump(monograms, myfile, ensure_ascii=False)
    with open('data/{}/bigrams_{}.json'.format(conf['iteration'], conf['iteration']), 'w', encoding='utf-8') as myfile:
        json.dump(bigrams, myfile, ensure_ascii=False)

    print('{} lexemes'.format(len(lexemes)))


if __name__ == '__main__':
    main()
