#!/usr/bin/php
<?php

# Help

if (count($argv) <= 1) {
	echo PHP_EOL;
	echo 'Usage:' . PHP_EOL;
	echo $argv[0] . ' get [PROJECT] [-d[DIR]]' . PHP_EOL;
    echo $argv[0] . ' merge [PROJECT] [-d[DIR]] [-p[FILE|URL] [-l[LOCALE]]' . PHP_EOL;
	echo PHP_EOL;
    echo 'Examples:' . PHP_EOL;
    echo $argv[0] . ' get opencart -d /path/to/opencart' . PHP_EOL;
    echo $argv[0] . ' merge opencart -d /path/to/opencart -p /path/to/opencart.po -l es-cl' . PHP_EOL;
    echo $argv[0] . ' merge opencart -d /path/to/opencart -p https://example.com/glotpress/projects/opencart/es-cl/default/ -l es-cl' . PHP_EOL;
    echo PHP_EOL;
	echo 'To get some more information, please visit: https://github.com/burbuja/bbl.' . PHP_EOL;
	exit;
}

# Validate action
if ($argv[1] == 'get' || $argv[1] == 'merge') {
    $action = $argv[1];
} else {
    echo 'This action is not supported!' . PHP_EOL;
	exit;
}

# Validate project
$projects = [
    'opencart',
];
if (in_array($argv[2], $projects)) {
    $project = $argv[2];
} else {
    echo 'This project is not supported!' . PHP_EOL;
    exit;
}

# Validate directory
$key = array_search('-d', $argv);
if ($key && array_key_exists($key + 1, $argv)) {
    $dn = realpath($argv[$key + 1]);
    $tdn = $dn . '_trans';
} else {
    echo 'Directory not specified!' . PHP_EOL;
    exit;
}
if (!is_dir($dn)) {
    echo 'Directory does not exist!' . PHP_EOL;
    exit;
}

# Validate .po file
$key = array_search('-p', $argv);
if ($key && array_key_exists($key + 1, $argv)) {
    $po = $argv[$key + 1];
} elseif ($action == 'merge') {
    echo 'PO file not specified!' . PHP_EOL;
    exit;
}

# Validate locale
$key = array_search('-l', $argv);
if ($key && array_key_exists($key + 1, $argv)) {
    $locale = $argv[$key + 1];
} elseif ($action == 'merge') {
    echo 'Locale not specified!' . PHP_EOL;
    exit;
}

# Extract translations
$po_patterns = [
	'~msgid\s"(.+)"\nmsgstr\s"(.+)"\n~',
];
if ($action == 'merge') {
    if ( preg_match( '~^https?\://~U', $po ) ) {
        $o = fopen($po . 'export-translations?format=po', 'r');
        $c = stream_get_contents($o);
    } elseif (file_exists($po)) {
        $o = fopen($po, 'r');
        $c = fread($o, filesize($po));
    } else {
        echo 'PO file does not exist!' . PHP_EOL;
        exit;
    }
    foreach ($po_patterns as $p)
        preg_match_all($p, $c, $matches, PREG_SET_ORDER);
    foreach ($matches as $m) {
        $d[]['original'] = $m[1];
        $d[array_key_last($d)]['translated'] = $m[2];
    }
}

# Create a list of files
function getFileList($dir, $array = []) {
	$files = array_diff(scandir($dir), array('.', '..'));
	foreach ($files as $file) {
		(is_dir("$dir/$file")) ? $array = getFileList("$dir/$file", $array) : $array[] = "$dir/$file";
	}
	return $array;
}
$fl = getFileList($dn);

# Execute action
switch ($project) {
    case 'opencart':
        switch ($action) {
            case 'get':
                # Extract phrases
                foreach ( $fl as $f ) {
                    if (
                        strstr($f, 'language/en-gb')
                        && pathinfo($f, PATHINFO_EXTENSION) == 'php'
                    ) {
                        include_once $f;
                        if (isset($_)) {
                            foreach ($_ as $k => $v) {
                                if ($k != 'text_terms') {
                                    $v = addslashes($v);
                                    $v = str_replace('\\\'', '\'', $v);
                                    $v = str_replace("\n", '\n', $v);
                                    if (empty($phrases) || !in_array($v, $phrases)) {
                                        $phrases[] = $v;
                                    }
                                }
                            }
                        }
                        unset($_);
                    }
                }
            break;
            case 'merge':
                # Validate locale

                # Split locale

                # Write .php files
                foreach ($fl as $f) {
                    # Write translated files
                    $f = str_replace('\\', '/', realpath($f));
                    if (
                        strstr($f, 'language/en-gb')
                        && pathinfo($f, PATHINFO_EXTENSION) == 'php'
                    ) {
                        include_once ($f);
                        if (isset($_)) {
                            $c = '<?php' .
                            PHP_EOL .
                            PHP_EOL;
                            foreach($_ as $k => $v) {
                                array_walk_recursive(
                                    $_,
                                    function (&$v, $k) {
                                        global $d;
                                        $dk = array_search($v, array_column($d, 'original'));
                                        if ($dk) {
                                            $v = $d[$dk]['translated'];
                                        }
                                    }
                                );
                                $c.= '$_[\'' . $k . '\'] = \'' . str_replace ( '\\"', '"', str_replace ( '\'', '\\\'', $_[$k])) . '\';' . "\n";
                            }
                            $f = str_replace('en-gb', $locale, $f);
                            $f = str_replace($dn, $tdn, $f);
                            if (!is_dir(pathinfo($f, PATHINFO_DIRNAME)))
                                mkdir(pathinfo($f, PATHINFO_DIRNAME), 0775, true);
                            $o = fopen ($f, 'w');
                            fwrite ($o, $c);
                            fclose ($o);
                            unset($_);
                        }
                    }
                }
                # Download flag
                if (!file_exists($tdn . '/upload/install/language/' . $locale . '/' . $locale . '.png')) {
                    $o = fopen('https://raw.githubusercontent.com/opencart/opencart/31323f8ce70338e88570217f76e1111f7b2bcc8f/upload/image/flags/cl.png', 'r');
                    $c = stream_get_contents($o);
                    fclose($o);
                    $o = fopen($tdn . '/upload/install/language/' . $locale . '/' . $locale . '.png', 'w');
                    fwrite ($o, $c);
                }
                copy(
                    $tdn . '/upload/install/language/' . $locale . '/' . $locale . '.png',
                    $tdn . '/upload/admin/language/' . $locale . '/' . $locale . '.png'
                );
                copy(
                    $tdn . '/upload/install/language/' . $locale . '/' . $locale . '.png',
                    $tdn . '/upload/catalog/language/' . $locale . '/' . $locale . '.png'
                );
                echo 'Translated files have been written in "' . $tdn . '".' . PHP_EOL;
            break;
        }
    break;
}

# Write a new .po file
if ($action == 'get'){
    if (count($phrases) != 0) {
        echo 'There are ' . count($phrases) . ' phrases obtained.' . PHP_EOL;
        $pofn = $project . '.po';
        $po = fopen($pofn, 'w+');
        fwrite($po, '# Generated by bbl.php' . PHP_EOL);
        fwrite($po, 'msgid ""' . PHP_EOL);
        fwrite($po, 'msgstr ""' . PHP_EOL);
        foreach ( $phrases as $p ) {
            $p = str_replace( '\\\'', "'", $p );
            $p = str_replace( "\n", '\n', $p );
            fwrite( $po, PHP_EOL );
            fwrite( $po, 'msgid "' . $p . '"' . PHP_EOL );
            fwrite( $po, 'msgstr ""' . PHP_EOL );
        }
        fclose($po);
        echo 'The file "' . $pofn . '" has been successfully created!' . PHP_EOL;
    } else {
        echo 'Phrases could not be obtained.' . PHP_EOL;
        exit;
    }

}