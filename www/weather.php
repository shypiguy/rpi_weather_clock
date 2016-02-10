<!DOCTYPE html>
<html>
<link rel="stylesheet" href="http://domain.tld/mobile.css" type="text/css" media="handheld" />
<head>
Weather Clock mode control
</head>
<body>

<?php
$myfile = fopen("setting.txt", "r");
$file_setting = fgets($myfile);
fclose($myfile);
?>

<form name="input" action="write_setting.php" method="get">
<input type="radio" name="setting" <?php if (isset($file_setting) && $file_setting=="relative_humidity\n") echo "checked";?>  value="relative_humidity">Relative Humidity<br>
<input type="radio" name="setting" <?php if (isset($file_setting) && $file_setting=="feelslike_f\n") echo "checked";?>  value="feelslike_f">Feels Like (degrees F)<br>
<input type="radio" name="setting" <?php if (isset($file_setting) && $file_setting=="dewpoint_f\n") echo "checked";?>  value="dewpoint_f">Dewpoint (degrees F)<br>
<input type="radio" name="setting" <?php if (isset($file_setting) && $file_setting=="precip_today_in\n") echo "checked";?>  value="precip_today_in">Precipitation Today (inches)<br>
<input type="radio" name="setting" <?php if (isset($file_setting) && $file_setting=="wind_gust_mph\n") echo "checked";?>  value="wind_gust_mph">Wind Gust (MPH)<br>
<input type="radio" name="setting" <?php if (isset($file_setting) && $file_setting=="visibility_mi\n") echo "checked";?>  value="visibility_mi">Visibility (Miles)<br>
<input type="submit" value="Submit">
</form>

</body>
</html>
