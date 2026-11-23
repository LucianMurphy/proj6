<?php

$API = "http://laptop-service";

$lists   = array("listAll" => "All times", "listOpenOnly" => "Open times only", "listCloseOnly" => "Close times only");
$formats = array("json", "csv");

$list   = isset($_GET["list"]) && array_key_exists($_GET["list"], $lists) ? $_GET["list"] : "listAll";
$format = isset($_GET["format"]) && in_array($_GET["format"], $formats) ? $_GET["format"] : "json";
$top    = isset($_GET["top"]) && $_GET["top"] !== "" ? (int) $_GET["top"] : null;

$url = "$API/$list/$format";
if ($top !== null) {
    $url .= "?top=$top";
}

$context  = stream_context_create(array("http" => array("ignore_errors" => true)));
$response = @file_get_contents($url, false, $context);

$error = null;
$rows  = array();   
$raw   = $response; 

if ($response === false) {
    $error = "Could not reach the API at $url";
} elseif ($format == "json") {
    $obj = json_decode($response, true);
    if (isset($obj["error"])) {
        $error = $obj["error"];
    } else {
        foreach ($obj["brevets"] as $brevet) {
            foreach ($brevet["controls"] as $control) {
                $rows[] = array_merge(array("distance" => $brevet["distance"]), $control);
            }
        }
    }
} else {
    $obj = json_decode($response, true); 
    if (isset($obj["error"])) {
        $error = $obj["error"];
    } else {
        $lines  = array_filter(explode("\n", trim($response)));
        $header = str_getcsv(array_shift($lines));
        foreach ($lines as $line) {
            $rows[] = array_combine($header, str_getcsv($line));
        }
    }
}

function h($text) {
    return htmlspecialchars((string) $text);
}
?>
<html>
    <head>
        <title>Brevet times</title>
    </head>

    <body>
        <h1>Brevet control times</h1>

        <form method="get">
            <select name="list">
                <?php foreach ($lists as $value => $label) { ?>
                    <option value="<?= $value ?>" <?= $value == $list ? "selected" : "" ?>><?= $label ?></option>
                <?php } ?>
            </select>

            <select name="format">
                <?php foreach ($formats as $f) { ?>
                    <option value="<?= $f ?>" <?= $f == $format ? "selected" : "" ?>><?= strtoupper($f) ?></option>
                <?php } ?>
            </select>

            Top <input type="number" name="top" min="1" value="<?= h($top) ?>" placeholder="all">

            <button type="submit">Show</button>
        </form>

        <p>Request: <code><?= h($url) ?></code></p>

        <?php if ($error) { ?>
            <p style="color: red;"><?= h($error) ?></p>
        <?php } elseif (count($rows) == 0) { ?>
            <p>No control times in the database yet. Submit some on the calculator page first.</p>
        <?php } else { ?>
            <table border="1" cellpadding="4">
                <tr>
                    <?php foreach (array_keys($rows[0]) as $column) { ?>
                        <th><?= h($column) ?></th>
                    <?php } ?>
                </tr>
                <?php foreach ($rows as $row) { ?>
                    <tr>
                        <?php foreach ($row as $value) { ?>
                            <td><?= h($value) ?></td>
                        <?php } ?>
                    </tr>
                <?php } ?>
            </table>
        <?php } ?>

        <h3>Raw response</h3>
        <pre><?= h($raw) ?></pre>
    </body>
</html>