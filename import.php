<?php

define('HENRY_USER_AGENT', 'Henry 1.2 (User:Envlh)');
define('HENRY_ITERATION', 8);
define('HENRY_DATA_PATH', 'data/'.HENRY_ITERATION.'/');
define('HENRY_RAW_DATA_PATH', HENRY_DATA_PATH.'raw/');

if (!file_exists(HENRY_DATA_PATH)) {
    mkdir(HENRY_RAW_DATA_PATH, 0777, true);
}

# existing lemmas

$existing_lemmas = array();

$url = 'https://query.wikidata.org/sparql?query='.urlencode('SELECT DISTINCT ?lemma { [] wikibase:lemma ?lemma ; dct:language wd:Q12107 }').'&format=json';
$res = json_decode(file_get_contents($url, false, stream_context_create([
    'socket' => ['bindto' => '0:0'], // force IPv4 (issue in sandbox used to run this code)
    'http' => ['header' => 'User-Agent: '.HENRY_USER_AGENT],
])))->results->bindings;

foreach ($res as $value) {
    $existing_lemmas[normalize_lemma($value->lemma->value)] = true;
}

# scraping

for ($page = 37; $page <= 313; $page++) {
    // $url = 'https://fr.wikisource.org/w/api.php?action=query&prop=revisions&titles='.urlencode('Page:Henry - Lexique étymologique du breton moderne.djvu/'.$page).'&rvslots=*&rvprop=content&formatversion=2&format=json';
    $url = 'https://fr.wikisource.org/w/api.php?action=parse&prop=wikitext&page='.urlencode('Page:Henry - Lexique étymologique du breton moderne.djvu/'.$page).'&formatversion=2&format=json';
    echo $url."\n";
    $content = file_get_contents($url, false, stream_context_create([
        'socket' => ['bindto' => '0:0'], // force IPv4 (issue in sandbox used to run this code)
        'http' => ['header' => 'User-Agent: '.HENRY_USER_AGENT],
    ]));
    file_put_contents(HENRY_RAW_DATA_PATH.'wikitext_'.$page.'.txt', json_decode($content)->parse->wikitext);
}

# merging

for ($page = 37; $page <= 313; $page++) {
    file_put_contents(HENRY_DATA_PATH.'wikitext_'.HENRY_ITERATION.'.txt', file_get_contents(HENRY_RAW_DATA_PATH.'/wikitext_'.$page.'.txt'), FILE_APPEND);
}

# cleaning

$content = file_get_contents(HENRY_DATA_PATH.'wikitext_'.HENRY_ITERATION.'.txt');

// removes html
// $content = strip_tags($content, '<ref><noinclude>'); // too many bugs with invalid content
// <references/></noinclude><noinclude><pagequality level="1" user="VIGNERON" />{{nr|270|TRÉAT-TRENK}}</noinclude>
$stringsToRemove = array('<references/>', '</noinclude>', '<noinclude>', '<nowiki/>', '<nowiki />');
foreach ($stringsToRemove as &$str) {
    $content = preg_replace('#'.preg_quote($str).'#i', '', $content);
}
$content = preg_replace('#<pagequality level="[0-9]+" user=".*?" />#i', '', $content);
$content = preg_replace('#<section (begin|end)=".*?"/>#i', '', $content);
$content = preg_replace('#<ref>.*?</ref>#im', '', $content);

// template {{nr}} entouré de retours à la ligne pour les séparer des autres lignes
$content = preg_replace('/\{\{nr\|(.*?)\}\}/i', "\n\n".'{{nr|$1}}'."\n\n", $content);

// removes template {{PetitTitre}}
$content = preg_replace('/\{\{PetitTitre\|.*?\}\}/i', '$1', $content);

// removes template {{corr}}
$content = preg_replace('/\{\{corr\|.*?\|(.*?)\}\}/i', '$1', $content);

// removes template {{abréviation}}
$content = preg_replace('/\{\{abréviation\|(.*?)\|.*?\}\}/i', '$1', $content);

// simple retour à la ligne => une seule ligne
$content = preg_replace('/'."\n".'([^'."\n".'])/', ' $1', $content);

// trim
$content = preg_replace('/'."\n".' +/', "\n", $content);
$content = preg_replace('/ +'."\n".'/', "\n", $content);

// removes template {{AN}}
$content = preg_replace('/^\{\{AN\|1\=(.*?)\}\}$/mi', '$1', $content);
$content = preg_replace('/^\{\{AN\|(.*?)\}\}$/mi', '$1', $content);
$content = preg_replace('/^\{\{AlinéaNégatif\|1\=(.*?)\}\}$/mi', '$1', $content);
$content = preg_replace('/^\{\{AlinéaNégatif\|(.*?)\}\}$/mi', '$1', $content);

// misc
$content = preg_replace('/^\{\{c\| LEXIQUE ÉTYMOLOGIQUE$/mi', '', $content);
$content = preg_replace('/^\DES TERMES LES PLUS USUELS DU BRETON MODERNE \}\}$/mi', '', $content);
$content = preg_replace('/^\{\{AlinéaNégatif\|/mi', '', $content);
$content = preg_replace('/^\{\{Séparateur\|lh\=2\}\}/mi', '', $content);
$content = preg_replace('/^\}\}$/mi', '', $content);
$content = preg_replace('/^\{\{c\|FIN\}\}$/mi', '', $content);

// double espace
$content = preg_replace('/  /', ' ', $content);

// double retour à la ligne
do {
    $content = preg_replace('/'."\n\n".'/i', "\n", $content);
} while (preg_match('/'."\n\n".'/i', $content));

// apostrophe droite
$content = str_replace('’', '\'', $content);

file_put_contents(HENRY_DATA_PATH.'stripped_'.HENRY_ITERATION.'.txt', $content);

# parsing

$lines = explode("\n", $content);

$lexemes = array();
$errors = array();
$already_exist = array();
$types = array();
$pageNumber = 1;
foreach ($lines as &$line) {
    $line = trim($line);
    if (preg_match('/^\'\'\'(.*?)\'\'\'(.*)/', $line, $match)) {
        $valid = true;
        $already_exists = false;
        $lexeme = new stdClass;
        $lexeme->page = $pageNumber;
        $forms = preg_replace('#^[0-9]+ #', '', $match[1]);
        $forms = explode(', ', $forms);
        $forms[0][0] = strtolower($forms[0][0]); // TODO É ; TODO 2e lettre après *
        $lexeme->lemma = $forms[0];
        $lexeme->forms = $forms;
        //$lexeme->language = 'Q12107';
        $lexeme->definition = $match[2];
        // lemma already exists in Wikidata
        if (isset($existing_lemmas[normalize_lemma($lexeme->lemma)])) {
            $already_exists = true;
        }
        elseif (preg_match('/^( \([CLTV., ]+\))?, ([a-zéè\' .]+)/', $lexeme->definition, $match)) {
            $dialect = trim($match[1]);
            $type = trim($match[2]);
            $lexeme->raw_nature = $type;
            switch ($type) {
                case 'adj.':
                    $lexeme->nature = 'Q34698';
                break;
                case 'adj. f.':
                    $lexeme->nature = 'Q34698';
                    $lexeme->gender = 'Q1775415';
                break;
                case 'adv.':
                    $lexeme->nature = 'Q380057';
                break;
                case 'loc. adv.':
                case 'locution adverbiale':
                    $lexeme->nature = 'Q5978303';
                break;
                case 'préfixe de direction':
                case 'préfixe général de conjugaison':
                case 'préfixe général de direction':
                case 'préfixe impliquant originairement conjonction':
                case 'préfixe inversif ou privatif':
                case 'préfixe perdu':
                case 'préfixe très commun au sens de':
                case 'préf.':
                case 'préf. augmentatif':
                case 'préf. impliquant originairement conjonction':
                case 'préf. itératif':
                case 'préf. local au sens de':
                case 'préf. péjoratif':
                case 'préf. péjoratif et diminutif':
                case 'préf. rare et de sens très indécis':
                case 'préf. verbal':
                case 'préf. verbal de direction':
                    $lexeme->nature = 'Q134830'; // préfixe
                break;
                case 'prép.':
                case 'prép. dans la locution':
                    $lexeme->nature = 'Q4833830';
                break;
                case 's. f.':
                case 's. f. pl.': // TODO
                    $lexeme->nature = 'Q1084';
                    $lexeme->gender = 'Q1775415';
                break;
                case 's. m.':
                case 's. m. pl.': // TODO
                    $lexeme->nature = 'Q1084';
                    $lexeme->gender = 'Q499327';
                break;
                case 's. m. f.':
                    $lexeme->nature = 'Q1084';
                break;
                case 'vb.':
                    $lexeme->nature = 'Q24905';
                break;
                default:
                    $valid = false;
            }
        }
        else {
            $valid = false;
        }
        if ($valid && !$already_exists) {
            $lexemes[] = $lexeme;
        } elseif (!$valid) {
            $errors[] = $lexeme;
            @$types[$lexeme->raw_nature]++;
        } elseif ($already_exists) {
            $already_exist[] = $lexeme;
        }
    }
    elseif (preg_match('/^\{\{nr\|/i', $line)) {
        $pageNumber++;
    }
}

save_lexemes(HENRY_DATA_PATH.'ok_'.HENRY_ITERATION.'.csv', $lexemes);
save_lexemes(HENRY_DATA_PATH.'ko_'.HENRY_ITERATION.'.csv', $errors);
save_lexemes(HENRY_DATA_PATH.'already_exist_'.HENRY_ITERATION.'.csv', $already_exist);

ksort($types);
print_r($types);

function save_lexemes($file_path, $lexemes) {
    $output = 'lemma,page,nature,gender,forms'."\n";
    foreach ($lexemes as &$lexeme) {
        $output .= $lexeme->lemma.','.$lexeme->page.','.@$lexeme->nature.','.@$lexeme->gender.',"'.implode($lexeme->forms, ',').'"'."\n";
    }
    file_put_contents($file_path, $output);
}

function normalize_lemma($lemma) {
    return preg_replace('/[^a-z]/', '', strtolower(iconv('UTF-8', 'US-ASCII//TRANSLIT', $lemma)));
}

?>