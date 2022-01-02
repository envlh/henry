<?php

$conf = json_decode(file_get_contents('conf/general.json'));

define('HENRY_USER_AGENT', $conf->user_agent);
define('HENRY_ITERATION', $conf->iteration);
define('HENRY_DATA_PATH', 'data/'.HENRY_ITERATION.'/');
define('HENRY_RAW_DATA_PATH', HENRY_DATA_PATH.'raw/');

if (!file_exists(HENRY_DATA_PATH)) {
    mkdir(HENRY_RAW_DATA_PATH, 0777, true);
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

?>