<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:msxsl="urn:schemas-microsoft-com:xslt" xmlns:user="http://android.riteshsahu.com">
<xsl:template match="/">
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

			.emoji {
				font-size: 18px;
				vertical-align: middle;
			}

			.message {
				min-width: 300px;
				width: 500px;
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
					<td class="date" style="display: none"><xsl:value-of select="@date"/></td>

					<td class="message">
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
			"use strict";

			var Cols = {
				TYPE: 0,
				NUMBER: 1,
				CONTACT: 2,
				DATE: 3,
				TIMESTAMP: 4,
				MESSAGE: 5,
			};

			var useMerged = false;

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

				for (var i = 1, len = tbl.rows.length; i < len; i++)
				{
					var row = tbl.rows[i];

					var status = row.cells[Cols.TYPE].textContent.trim();

					//color by status
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

					//format multiple numbers by newlines
					row.cells[Cols.NUMBER].textContent = row.cells[Cols.NUMBER].textContent.replace(/~/g, "\n");

					var mms_sender = row.cells[Cols.MESSAGE].getElementsByClassName("mms-sender")[0];
					if(mms_sender !== undefined)
					{
						var numspl = row.cells[Cols.NUMBER].textContent.split("\n");
						if(numspl.length > 1)
						{
							//if it's a group text, put the sender in bold

							var ctspl = row.cells[Cols.CONTACT].textContent.split(", ");
							var changed = ctspl.length < numspl.length;

							//if numspl and ctspl lengths are not equal, then at least one number is not a contact, it's probably in order
							while(ctspl.length < numspl.length)
								ctspl.push("(Unknown)");

							for (var n = 0; n < numspl.length; n++)
							{
								var num = numspl[n].replace(/[^0-9]/g, "");
								var sender = mms_sender.innerHTML;

								if(num == sender || (num.length >= 10 && num.substring(num.length - 10) == sender.substring(sender.length - 10)))
								{
									numspl[n] = '<b>' + numspl[n] + '</b>';
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
				//store last selected
				var oldcontact = conv.selectedIndex > 0 ? contacts[conv.selectedIndex - 1][1] : undefined;
				var oldconvstr = conv.options[conv.selectedIndex].value;

				var selected = 0;
				var curidx = 1;

				while(conv.options.length > 1)
					conv.removeChild(conv.options[1]);

				var added = new Set();

				for (var i = 0; i < contacts.length; i++)
				{
					var option = document.createElement("option");
					var str;

					if(useMerged && contacts[i][1] != "(Unknown)")
					{
						str = contacts[i][1];
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

					//restore last selected
					if(useMerged && (contacts[i][1] != "(Unknown)" && contacts[i][1] == oldcontact || str == oldconvstr))
					{
						selected = curidx;
					}

					//only increment if not in added set
					curidx++;
				}

				conv.selectedIndex = selected;
			}

			function filterTable(tbl, conv, contacts)
			{
				var selectedNum = undefined;
				var selectedContact = undefined;
				var idx = conv.selectedIndex;

				if(idx > 0)
				{
					var convstr = conv.options[idx].value;
					if(!useMerged || convstr.startsWith("(Unknown) "))
					{
						var spl = convstr.split(" - ");
						selectedNum = spl[spl.length - 1];
					}else
					{
						selectedContact = convstr;
					}
				}

				var total = 0;

				for (var i = 1, len = tbl.rows.length; i < len; i++)
				{
					var row = tbl.rows[i];
					var num = row.cells[Cols.NUMBER].textContent;
					var ct = row.cells[Cols.CONTACT].textContent;

					if((selectedNum == undefined || num == selectedNum) && (selectedContact == undefined || ct == selectedContact))
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

						var idxoff = idx + 6;
						var highsurr = parseInt(str.substring(idxoff, idxoff + 5), 10);
						idxoff += 5 + 7;
						var lowsurr = parseInt(str.substring(idxoff, idxoff + 5), 10);

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
			document.getElementById("textsshown").innerHTML = smses.rows.length - 1;

			unescapeSurrogates(smses);

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
