 <!DOCTYPE html>
<html>
<body>
<head>
<meta http-equiv="Refresh" content="5;url=weather.php">
<?php
$myfile = fopen("setting.txt", "w") or die("Unable to open file!");
$txt = $_GET["setting"] . "\n";
fwrite($myfile, $txt);
fclose($myfile);
?> 
<p>Setting updated!</p>
<p>Click here to go back to the <a href="weather.php">settings page</a></p>
<p>You will be redirected to the settings page in 5 seconds.</p>
<p>If you see this message for more than 5 seconds, please click on the link above!</p>
</body>

</body>
</html>


