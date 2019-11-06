<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:msxsl="urn:schemas-microsoft-com:xslt" xmlns:user="http://android.riteshsahu.com">
<xsl:template match="/">
	<html>
	<head>
		<style>
			body {
				font-family: arial, sans-serif;
				color: #000;
				font-size: 13px;
				color: #333;
			}

			table {
				font-size: 1em;
				margin: 0 0 1em;
				border-collapse: collapse;
				border-width: 0;
				empty-cells: show;
			}

			td, th {
				border: 1px solid #ccc;
				padding: 6px 12px;
				text-align: left;
				vertical-align: top;
				background-color: inherit;
			}

			th {
				background-color: #dee8f1;
			}
		</style>
	</head>
	<body>
		<h2>Phone calls</h2>
		<p>Calls Shown: <span id="callsshown">0</span></p>

		<table id="calls">
			<tr>
				<th>Type</th>
				<th>Number</th>
				<th>Contact</th>
				<th>Date</th>
				<th>Duration</th>
			</tr>
			<xsl:for-each select="calls/call">
				<tr>
					<td>
						<xsl:choose>
							<xsl:when test="@type = 1">
								Incoming
							</xsl:when>
							<xsl:when test="@type = 2">
								Outgoing
							</xsl:when>
							<xsl:when test="@type = 3">
								Missed
							</xsl:when>
							<xsl:when test="@type = 4">
								Voicemail
							</xsl:when>
							<xsl:when test="@type = 5">
								Rejected
							</xsl:when>
							<xsl:when test="@type = 6">
								Refused List
							</xsl:when>

							<xsl:otherwise>
								<xsl:value-of select="@type"/>Unknown
							</xsl:otherwise>
						</xsl:choose>
					</td>
					<td><xsl:value-of select="@number"/></td>
					<td><xsl:value-of select="@contact_name"/></td>
					<td><xsl:value-of select="@readable_date"/></td>
					<td class="date" style="display: none"><xsl:value-of select="@date"/><br/></td>
					<td><xsl:value-of select="@duration"/></td>
				</tr>
			</xsl:for-each>
		</table>

		<script>
		<![CDATA[
			var Cols = {
				TYPE: 0,
				NUMBER: 1,
				CONTACT: 2,
				DATE: 3,
				TIMESTAMP: 4,
				DURATION: 5,
			};

			function prepareTable(tbl)
			{
				var rows = Array.from(tbl.rows);
				rows.splice(0, 1);

				rows.sort(function(a, b){
					//sort by hidden date value
					a = parseInt(a.getElementsByClassName("date")[0].innerHTML, 10);
					b = parseInt(b.getElementsByClassName("date")[0].innerHTML, 10);

					if(a < b)
						return -1;
					if(a > b)
						return 1;
					return 0;
				});

				var tbody = tbl.getElementsByTagName("tbody")[0];

				//remove all but header, and create rows back as sorted
				while(tbody.children.length > 1)
					tbody.removeChild(tbody.children[1]);
				for (var i = 0; i < rows.length; i++)
					tbody.appendChild(rows[i]);

				for (i = 1, len = tbl.rows.length; i < len; i++)
				{
					var row = tbl.rows[i];

					var status = row.cells[Cols.TYPE].textContent.trim();

					switch(status)
					{
						case "Incoming":
							break;
						case "Outgoing":
							row.style.backgroundColor = "#b0ffb0";
							break;
						case "Missed":
							row.style.backgroundColor = "#c0c0ff";
							break;
						case "Voicemail":
							row.style.backgroundColor = "#c0c0ff";
							break;
						case "Rejected":
							row.style.backgroundColor = "#ffb0b0";
							break;
						case "Refused List":
							row.style.backgroundColor = "#ffb0b0";
							break;
					}

					var time = parseInt(row.cells[Cols.DURATION].textContent.trim());

					var hour = Math.floor(time / 3600);
					time %= 3600;
					var min = Math.floor(time / 60);
					time %= 60;

					if(hour > 0)
					{
						row.cells[Cols.DURATION].textContent = hour + "h " + min + "m " + time + "s";
					}else
					if(min > 0)
					{
						row.cells[Cols.DURATION].textContent = min + "m " + time + "s";
					}else
					{
						row.cells[Cols.DURATION].textContent = time + "s";
					}
				}
			}

			var calls = document.getElementById("calls");

			prepareTable(calls);

			document.getElementById("callsshown").innerHTML = calls.rows.length - 1;
		]]>
		</script>
	</body>
	</html>
</xsl:template>
</xsl:stylesheet>
