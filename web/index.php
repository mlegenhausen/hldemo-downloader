<?php
function formatBytes($bytes, $precision = 2) { 
    $units = array('B', 'KB', 'MB', 'GB', 'TB'); 
   
    $bytes = max($bytes, 0); 
    $pow = floor(($bytes ? log($bytes) : 0) / log(1024)); 
    $pow = min($pow, count($units) - 1); 
   
    $bytes /= pow(1024, $pow); 
   
    return round($bytes, $precision) . ' ' . $units[$pow]; 
} 

function cmp($a, $b) {
	return -1 * strcmp($a["date"], $b["date"]);
}

$dir = ".";
$today = date("d.m.Y");
if ($dh = opendir($dir)) {
	$items = array();
    while (($file = readdir($dh)) !== false) {
    	if (preg_match("/^([0-9]{4})([0-9]{2})([0-9]{2})-([0-9]{2})([0-9]{2})-(\\w+)\.zip$/", $file, $match)) {
    		$date = $match[3].".".$match[2].".".$match[1];
    		$time = $match[4].":".$match[5];
    		$map = $match[6];
    		$size = formatBytes(filesize($file));
    		$class = strcmp($date, $today) ? "odd gradeA" : "gradeX";
    		$item = array("date" => $date, "time" => $time, "map" => $map, "size" => $size, "file" => $file, "class" => $class);
    		$items[] = $item;
    	}
    }
    closedir($dh);
    usort($items, "cmp");
}
?>

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
	<head>
		<meta http-equiv="content-type" content="text/html; charset=utf-8" />
		
		<title>Demos</title>
		<style type="text/css" title="currentStyle">
			@import "media/css/demo_page.css";
			@import "media/css/demo_table_jui.css";
			@import "media/themes/smoothness/jquery-ui-1.8.4.custom.css";
		</style>
		<script type="text/javascript" language="javascript" src="media/js/jquery.js"></script>
		<script type="text/javascript" language="javascript" src="media/js/jquery.dataTables.js"></script>
		<script type="text/javascript" charset="utf-8">
			function trim(str) {
				str = str.replace(/^\s+/, '');
				for (var i = str.length - 1; i >= 0; i--) {
					if (/\S/.test(str.charAt(i))) {
						str = str.substring(0, i + 1);
						break;
					}
				}
				return str;
			}
			function transform(a) {
				var x = 10000000000000;
				if (trim(a) != '') {
					var frDatea = trim(a).split(' ');
					var frTimea = frDatea[1].split(':');
					var frDatea2 = frDatea[0].split('.');
					x = (frDatea2[2] + frDatea2[1] + frDatea2[0] + frTimea[0] + frTimea[1]) * 1;
				}
				return x;
			}

			function sort(a, b) {
				var x = transform(a);
				var y = transform(b);
				return ((x < y) ? -1 : ((x > y) ? 1 : 0));
			}
	
			jQuery.fn.dataTableExt.oSort['date-euro-asc'] = function(a, b) {
				return sort(a, b);
			};
	
			jQuery.fn.dataTableExt.oSort['date-euro-desc'] = function(a, b) {
				return sort(a, b) * -1;
			};
			
			$(document).ready(function() {
				$('#example').dataTable({
					"bJQueryUI": true,
					"iDisplayLength": 25,
					"aLengthMenu": [[25, 50, 100, -1], [25, 50, 100, "All"]],
					"sPaginationType": "full_numbers",
					"aaSorting": [[ 1, "desc" ]],
					"aoColumns": [
						null,
						{ "sType": "date-euro" },
					  	null,
					  	null
					]
				});
			} );
		</script>
	</head>
	<body id="dt_example">
		<div id="container">			
			<h1>Demos</h1>
			<p>This demo page will synchronized hourly with our game server. All demos older than 90 days will be deleted.
			All demos that were added today are red highlighted.</p>
			<div id="demo_jui">
				<table cellpadding="0" cellspacing="0" border="0" class="display" id="example">
					<thead>
						<tr>
							<th>Filename</th>
							<th>Date</th>
							<th>Map</th>
							<th>Size</th>
						</tr>
					</thead>
					<tbody>
						<?php 
						for ($i = 0; $i < count($items); $i++) {
							echo "<tr class=\"".$items[$i]["class"]."\">";
							echo "<td><a href=\"".$items[$i]["file"]."\">".$items[$i]["file"]."</a></td>";
							echo "<td align=\"center\">".$items[$i]["date"]." ".$items[$i]["time"]."</td>";
							echo "<td>".$items[$i]["map"]."</td>";
							echo "<td align=\"right\">".$items[$i]["size"]."</td>";
							echo "</tr>";
						}
						?>
					</tbody>
				</table>
			</div>
		</div>
	</body>
</html>