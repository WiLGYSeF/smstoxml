<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:msxsl="urn:schemas-microsoft-com:xslt" xmlns:user="http://android.riteshsahu.com">
<xsl:template match="/">
<html>
<head>
	<style>
		body {
			font-family: arial,sans-serif;
		}

		p, span {
			font-size: 14px;
		}

		table {
			border-collapse: collapse;
			border-width: 0;

			empty-cells: show;
		}

		td, th {
			border: 1px solid #ccc;
			font-size: 13px;
			text-align: left;

			padding: 10px;
			white-space: pre-wrap;
		}

		th {
			background-color: #86bbf0;
		}

		tr[data-type='Outgoing'] {
			background-color: #b0ffb0;
		}

		tr[data-type='Missed'] {
			background-color: #c0c0ff;
		}

		tr[data-type='Voicemail'] {
			background-color: #c0c0ff;
		}

		tr[data-type='Rejected'] {
			background-color: #ffb0b0;
		}

		tr[data-type='Refused List'] {
			background-color: #ffb0b0;
		}

		.duration {
			text-align: right;
		}
	</style>
</head>
<body>
	<h1>Phone Calls</h1>

	<span>Contacts: </span>
	<select id="contacts">
		<option text="All Contacts"></option>
	</select>

	<p>Calls Shown: <span id="callsShown">0</span></p>

	<table id="calls">
		<tr>
			<th>Type</th>
			<th>Number</th>
			<th>Contact</th>
			<th>Date</th>
			<th>Duration</th>
		</tr>
		<xsl:for-each select="calls/call">
			<xsl:sort select="date" />

			<xsl:variable name="typeStr">
				<xsl:choose>
					<xsl:when test="@type = 1">Incoming</xsl:when>
					<xsl:when test="@type = 2">Outgoing</xsl:when>
					<xsl:when test="@type = 3">Missed</xsl:when>
					<xsl:when test="@type = 4">Voicemail</xsl:when>
					<xsl:when test="@type = 5">Rejected</xsl:when>
					<xsl:when test="@type = 6">Refused List</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="@type"/>Unknown
					</xsl:otherwise>
				</xsl:choose>
			</xsl:variable>

			<tr data-contact_name="{@contact_name}" data-duration="{@duration}" data-number="{@number}" data-timestamp="{@date}" data-type="{$typeStr}">
				<td>
					<xsl:value-of select="$typeStr"/>
				</td>
				<td class="number"><xsl:value-of select="@number"/></td>
				<td><xsl:value-of select="@contact_name"/></td>
				<td><xsl:value-of select="@readable_date"/></td>
				<td class="duration"><xsl:value-of select="@duration"/></td>
			</tr>
		</xsl:for-each>
	</table>

	<script>
	<![CDATA[
		let callsTable = document.getElementById("calls");
		let contactsSelect = document.getElementById("contacts");

		function getContactList(tbl)
		{
			let contactList = {};

			for (let i = 1; i < tbl.rows.length; i++)
			{
				let row = tbl.rows[i];
				contactList[row.dataset.number] = row.dataset.contact_name;
			}

			return contactList;
		}

		function filterTable(tbl, address)
		{
			let visible = 0;
			for (let i = 1; i < tbl.rows.length; i++)
			{
				let row = tbl.rows[i];

				if(address === undefined || row.dataset.number == address)
				{
					row.style.display = "";
					visible++;
				}else
				{
					row.style.display = "none";
				}
			}

			return visible;
		}

		function updateTable(tbl)
		{
			function ps(x)
			{
				return x.toString().padStart(2, "0");
			}

			for (let i = 1; i < tbl.rows.length; i++)
			{
				let row = tbl.rows[i];
				let duration = row.getElementsByClassName("duration")[0];

				let time = parseInt(row.dataset.duration);
				let timestr = "";

				if(time > 3600)
				{
					timestr += `${ps((time / 3600) >> 0)}h`;
					time %= 3600;
				}

				if(time > 60 || timestr.length != 0)
				{
					timestr += ` ${ps((time / 60) >> 0)}m`;
					time %= 60;
				}

				if(time >= 0 || timestr.length != 0)
				{
					timestr += ` ${ps(time)}s`;
				}

				timestr = timestr.trim();
				if(timestr[0] == "0")
					timestr = timestr.substring(1);

				duration.innerHTML = timestr;
			}
		}

		function updateContacts(contactList)
		{
			while(contactsSelect.firstChild)
				contactsSelect.removeChild(contactsSelect.lastChild);

			let option = document.createElement("option");
			option.text = "All Contacts";
			contactsSelect.add(option);

			for (let num in contactList)
			{
				option = document.createElement("option");
				option.dataset.address = num;
				option.dataset.contact_name = contactList[num];
				option.text = `${num}: ${contactList[num]}`;
				contactsSelect.add(option);
			}
		}

		function updateCount(tbl, c)
		{
			if(c === undefined)
			{
				c = 0;
				for (let i = 1; i < tbl.rows.length; i++)
				{
					if(tbl.rows[i].style.display == "")
						c++;
				}
			}

			document.getElementById("callsShown").innerHTML = c;
		}

		contactsSelect.addEventListener("change", function(e){
			let option = e.target.selectedOptions[0];

			updateCount(callsTable, filterTable(callsTable, option.dataset.address));
		});

		let contactList = getContactList(callsTable);

		updateTable(callsTable);
		updateContacts(contactList);
		updateCount(callsTable, undefined);
	]]>
	</script>
</body>
</html>
</xsl:template>
</xsl:stylesheet>
