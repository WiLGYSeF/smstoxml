<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:msxsl="urn:schemas-microsoft-com:xslt"
	xmlns:user="http://android.riteshsahu.com">
<xsl:template match="/">

	<!-- <xsl:text disable-output-escaping='yes'>&lt;!DOCTYPE html&gt;</xsl:text> -->
	<html>
	<head>
		<style>
			body {
				color: #333333;
				font-family: arial,sans-serif;
				font-size: 13px;
			}

			img {
				max-width: 300px;
				max-height: 240px;
			}

			table {
				border-collapse: collapse;
				border-width: 0;
				empty-cells: show;
				font-size: 1em;
				margin: 0 0 1em;
			}

			td, th {
				background-color: inherit;
				border: 1px solid #ccc;
				font-size: 13px;
				padding: 5px 10px;
				text-align: left;
				vertical-align: middle;
				white-space: pre-line;
			}

			th {
				background-color: #dee8f1;
			}

			tr td:nth-child(5) {
				display: none;
			}

			.emoji {
				font-size: 18px;
				vertical-align: middle;
			}

			.mms-sender {
				display: none;
			}
		</style>
	</head>
	<body>
		<h1>Messages</h1>

		<label for="conversations" style="font-size: 14px; margin-right: 8px">Conversations: </label>
		<select id="conversations" style="margin-bottom: 10px">
			<option id="all-conv" selected="selected">All Contacts</option>
		</select>
		<br />
		<input id="merge" type="button" value="Merge by Contact Name" />
		<p>Texts Shown: <span id="textsshown">0</span></p>

		<table id="smses">
			<colgroup>
				<col style=""/>
				<col style=""/>
				<col style=""/>
				<col style=""/>
				<col style="min-width: 300px; width: 500px"/>
			</colgroup>
			<tr>
				<th>Type</th>
				<th>Number</th>
				<th>Contact</th>
				<th>Date</th>
				<th>Message</th>
			</tr>
			<xsl:for-each select="smses/*">
				<tr>
					<xsl:choose>
						<xsl:when test="name() = 'sms'">
							<td>
								<xsl:if test="@type = 1">
									Received
								</xsl:if>
								<xsl:if test="@type = 2">
									Sent
								</xsl:if>
								<xsl:if test="@type = 3">
									Draft
								</xsl:if>
							</td>
						</xsl:when>
						<xsl:otherwise>
							<td>
								<xsl:if test="@msg_box = 1">
									Received
								</xsl:if>
								<xsl:if test="@msg_box = 2">
									Sent
								</xsl:if>
								<xsl:if test="@msg_box = 3">
									Draft
								</xsl:if>
							</td>
						</xsl:otherwise>
					</xsl:choose>

					<td><xsl:value-of select="@address"/></td>
					<td><xsl:value-of select="@contact_name"/></td>
					<td><xsl:value-of select="@readable_date"/></td>
					<td><xsl:value-of select="@date"/></td>

					<td>
						<xsl:choose>
							<xsl:when test="name() = 'sms'">
								<xsl:value-of select="@body"/>
							</xsl:when>
							<xsl:otherwise>
								<xsl:for-each select="addrs/addr">
									<xsl:if test="@type = '137'">
										<span class="mms-sender"><xsl:value-of select="@address"/></span>
									</xsl:if>
								</xsl:for-each>

								<xsl:for-each select="parts/part">
									<xsl:choose>
										<xsl:when test="@ct = 'application/smil'">
										</xsl:when>
										<xsl:when test="@ct = 'text/plain'">
											<xsl:value-of select="@text"/><br/>
										</xsl:when>
										<xsl:when test="starts-with(@ct,'image/')" >
											<img>
												<xsl:attribute name="src">
													<xsl:value-of select="concat(concat('data:',@ct), concat(';base64,',@data))"/>
												</xsl:attribute>
											</img><br/>
										</xsl:when>
										<xsl:otherwise>
											<i>Preview of <xsl:value-of select="@ct"/> not supported.</i><br/>
										</xsl:otherwise>
									</xsl:choose>
								</xsl:for-each>
							</xsl:otherwise>
						</xsl:choose>
					</td>
				</tr>
			</xsl:for-each>
		</table>

		<script>
		<![CDATA[
			"use strict;"

			var Cols = {
				TYPE: 0,
				NUMBER: 1,
				CONTACT: 2,
				DATE: 3,
				TIMESTAMP: 4,
				MESSAGE: 5
			};

			var useMerged = false;

			function prepareTable(tbl)
			{
				var rows = Array.from(tbl.rows);
				rows.splice(0, 1);

				rows.sort(function(a, b){
					a = parseInt(a.children[4].innerHTML, 10);
					b = parseInt(b.children[4].innerHTML, 10);

					if(a < b)
						return -1;
					if(a > b)
						return 1;
					return 0;
				});

				var tbody = tbl.getElementsByTagName("tbody")[0];

				while(tbody.children.length > 1)
					tbody.removeChild(tbody.children[1]);
				for (var i = 0; i < rows.length; i++)
					tbody.appendChild(rows[i]);

				for (var i = 1, len = tbl.rows.length; i < len; i++)
				{
					var row = tbl.rows[i];

					var status = row.cells[Cols.TYPE].textContent.trim();

					switch(status)
					{
						case "Received":
							status = "Recv";
							break;
						case "Sent":
							row.style.backgroundColor = "#b0ffb0";
							break;
						case "Draft":
							row.style.backgroundColor = "#ffffb0";
							break;
					}

					row.cells[Cols.TYPE].textContent = status;

					row.cells[Cols.NUMBER].textContent = row.cells[Cols.NUMBER].textContent.replace(/~/g, "\n");

					//highlight (bold) mms sender

					var mms_sender = row.cells[Cols.MESSAGE].getElementsByClassName("mms-sender")[0];
					if(mms_sender !== undefined)
					{
						var numspl = row.cells[Cols.NUMBER].textContent.split("\n");
						if(numspl.length > 1)
						{
							var ctspl = row.cells[Cols.CONTACT].textContent.split(", ");
							var changed = false;

							for (var n = 0; n < numspl.length; n++)
							{
								var num = numspl[n].replace(/[^0-9]/g, "");
								var sender = mms_sender.innerHTML;

								if(num == sender || (num.length >= 10 && num.substring(num.length - 10) == sender.substring(sender.length - 10)))
								{
									numspl[n] = '<b>' + numspl[n] + '</b>';
									if(ctspl.length == numspl.length)
										ctspl[n] = '<b>' + ctspl[n] + '</b>';
									changed = true;
									break;
								}
							}

							if(changed)
							{
								row.cells[Cols.NUMBER].innerHTML = numspl.join("\n");
								row.cells[Cols.CONTACT].innerHTML = ctspl.join(", ");
							}
						}
					}
				}
			}

			function getContacts(tbl)
			{
				var contacts = [];
				var numset = new Set();

				for (var i = 1, len = tbl.rows.length; i < len; i++)
				{
					var row = tbl.rows[i];
					var num = row.cells[Cols.NUMBER].textContent;
					var ct = row.cells[Cols.CONTACT].textContent;

					if(!numset.has(num))
					{
						contacts.push([num, ct]);
						numset.add(num);
					}
				}

				contacts.sort(function(a, b){
					if(a[1] < b[1])
						return -1;
					if(a[1] > b[1])
						return 1;
					return 0;
				});

				return contacts;
			}

			function populateConversations(conv, contacts)
			{
				var oldcontact = conv.selectedIndex >= 1 ? contacts[conv.selectedIndex - 1][1] : undefined;

				while(conv.options.length > 1)
					conv.removeChild(conv.options[1]);

				conv.selectedIndex = 0;

				var added = new Set();
				var option;
				var str;

				for (var i = 0; i < contacts.length; i++)
				{
					option = document.createElement("option");

					if(useMerged)
					{
						str = contacts[i][1];
						if(str == "(Unknown)")
							str += " - " + contacts[i][0];
					}else
					{
						str = contacts[i][1] + " - " + contacts[i][0];
					}

					if(added.has(str))
						continue;

					option.value = str;
					option.text = str;
					added.add(str);

					conv.add(option);

					if(useMerged && contacts[i][1] == oldcontact)
						conv.selectedIndex = i + 1;
				}
			}

			function filterTable(tbl, conv, contacts)
			{
				var idx = conv.selectedIndex;
				var selnum = undefined;
				var selct = undefined;

				if(idx > 0)
				{
					idx--;

					selct = contacts[idx][1];
					if(!useMerged || selct == "(Unknown)")
						selnum = contacts[idx][0];
				}

				var total = 0;

				for (var i = 1, len = tbl.rows.length; i < len; i++)
				{
					var row = tbl.rows[i];
					var num = row.cells[Cols.NUMBER].textContent;
					var ct = row.cells[Cols.CONTACT].textContent;

					if((selnum === undefined || num == selnum) && (selct === undefined || ct == selct))
					{
						row.style.display = "";
						total++;
					}else
					{
						row.style.display = "none";
					}
				}

				document.getElementById("textsshown").innerHTML = total;
			}

			function unescapeSurrogates(tbl)
			{
				//high surrogate: 0xd800 - 0xdbff
				//low surrogate: 0xdc00 - 0xdfff
				var re = new RegExp(/&amp;#5(?:5(?:29[6-9]|[3-9]\d\d)|6\d\d\d|7[0-2]\d\d|73[0-3]\d|734[0-3]);/);
			/*
				var unicodeToEmoji = {
					"\u263a": "&amp;#55357;&amp;#56898;", //smiling face

				};
			*/
				for (var i = 1, len = tbl.rows.length; i < len; i++)
				{
					var row = tbl.rows[i];
					var str = row.cells[Cols.MESSAGE].innerHTML;
					var msg = "";

					while(true)
					{
						var idx = str.search(re);
						if(idx == -1)
						{
							msg += str;
							break;
						}

						//look for second surrogate
						if(str.substring(idx + 12).search(re) != 0)
						{
							msg += str.substring(0, 12);
							str = str.substring(12);
							continue;
						}

						var highsurr = parseInt(str.substring(idx + 6, idx + 6 + 5), 10);
						var lowsurr = parseInt(str.substring(idx + 6 + 5 + 7, idx + 6 + 5 + 7 + 5), 10);

						if(!isNaN(highsurr) && !isNaN(lowsurr))
						{
							msg += str.substring(0, idx) + '<span class="emoji">' + String.fromCodePoint(highsurr) + String.fromCodePoint(lowsurr) + '</span>';
							str = str.substring(idx + 24);
						}else
						{
							msg += str.substring(0, idx + 24);
							str = str.substring(idx + 24);
						}
					}

					row.cells[Cols.MESSAGE].innerHTML = msg;
				}
			}

			var smses = document.getElementById("smses");
			var conv = document.getElementById("conversations");

			prepareTable(smses);

			var contacts = getContacts(smses);

			populateConversations(conv, contacts);

			unescapeSurrogates(smses);

			document.getElementById("textsshown").innerHTML = smses.rows.length - 1;

			document.getElementById("merge").addEventListener("click", function(e){
				e.target.disabled = true;
				useMerged = true;

				populateConversations(conv, contacts);
				filterTable(smses, conv, contacts);
			});

			conv.addEventListener("change", function(e){
				filterTable(smses, conv, contacts);
			});
		]]>
		</script>
	</body>
	</html>
</xsl:template>
</xsl:stylesheet>
