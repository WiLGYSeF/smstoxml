<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:msxsl="urn:schemas-microsoft-com:xslt" xmlns:user="http://android.riteshsahu.com">
<xsl:template match="/">
<html>
<head>
	<style type="text/css">
		body {
			font-family: arial,sans-serif;
		}

		img {
			max-width: 300px;
			max-height: 240px;
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

		tr[data-type='Sent'] {
			background-color: #b0ffb0;
		}

		tr[data-type='Draft'] {
			background-color: #fafabb;
		}

		.address .receiver, .contact_name .receiver {
			color: #444444;
			font-size: 13px;
		}

		.message {
			min-width: 300px;
			width: 500px;
		}
	</style>
</head>
<body>
	<h1>Messages</h1>

	<span>Contacts: </span>
	<select id="contacts">
		<option text="All Contacts"></option>
	</select>

	<p>Texts shown: <span id="textsShown">0</span></p>

	<table id="entry-table">
		<tr>
			<th>Type</th>
			<th>Number</th>
			<th>Contact</th>
			<th>Date</th>
			<th>Message</th>
		</tr>
		<xsl:for-each select="smses/*">
			<xsl:sort select="@date" />

			<xsl:variable name="ptype">
				<xsl:choose>
					<xsl:when test="name() = 'sms'">
						<xsl:value-of select="@type"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="@msg_box"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:variable>
			<xsl:variable name="typeStr">
				<xsl:choose>
					<xsl:when test="$ptype = 1">Recv</xsl:when>
					<xsl:when test="$ptype = 2">Sent</xsl:when>
					<xsl:when test="$ptype = 3">Draft</xsl:when>
					<xsl:otherwise></xsl:otherwise>
				</xsl:choose>
			</xsl:variable>

			<xsl:variable name="sender">
				<xsl:choose>
					<xsl:when test="name() = 'sms'">
						<xsl:if test="$typeStr = 'Recv'">
							<xsl:value-of select="@address"/>
						</xsl:if>
					</xsl:when>
					<xsl:otherwise>
						<xsl:for-each select="addrs/addr">
							<xsl:if test="@type = '137'">
								<xsl:value-of select="@address"/>
							</xsl:if>
						</xsl:for-each>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:variable>

			<tr data-address="{@address}" data-contact_name="{@contact_name}" data-sender="{$sender}" data-type="{$typeStr}">
				<td><xsl:value-of select="$typeStr"/></td>
				<td class="address"><xsl:value-of select="@address"/></td>
				<td class="contact_name"><xsl:value-of select="@contact_name"/></td>
				<td><xsl:value-of select="@readable_date"/></td>
				<td class="message">
					<xsl:choose>
						<xsl:when test="name() = 'sms'">
							<xsl:value-of select="@body"/>
						</xsl:when>
						<xsl:otherwise>
							<xsl:for-each select="parts/part">
								<xsl:choose>
									<xsl:when test="@ct = 'application/smil'">
									</xsl:when>
									<xsl:when test="@ct = 'text/plain'">
										<xsl:value-of select="@text"/><br/>
									</xsl:when>
									<xsl:when test="starts-with(@ct,'image/')" >
										<img height="300">
											<xsl:attribute name="src">
												<xsl:value-of select="concat(concat('data:',@ct), concat(';base64,',@data))"/>
											</xsl:attribute>
										</img>
										<br/>
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

		let entryTable = document.getElementById("entry-table");
		let contactsSelect = document.getElementById("contacts");

		function getContactList(tbl)
		{
			let contactList = {};

			for (let i = 1; i < tbl.rows.length; i++)
			{
				let row = tbl.rows[i];
				contactList[row.dataset.address] = row.dataset.contact_name;
			}

			return contactList;
		}

		function filterTable(tbl, address)
		{
			let visible = 0;
			for (let i = 1; i < tbl.rows.length; i++)
			{
				let row = tbl.rows[i];

				if(address === undefined || row.dataset.address == address)
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
			for (let i = 1; i < tbl.rows.length; i++)
			{
				let row = tbl.rows[i];
				let address = row.getElementsByClassName("address")[0];
				let contact_name = row.getElementsByClassName("contact_name")[0];

				let numbers = address.innerHTML.split("~");
				let contacts = contact_name.innerHTML.split(", ");

				if(numbers.length > 1)
				{
					for (let n = 0; n < numbers.length; n++)
					{
						if(numbers[n] == row.dataset.sender || numbers[n].endsWith(row.dataset.sender))
						{
							numbers[n] = `<b>${numbers[n]}</b>`;
							contacts[n] = `<b>${contacts[n]}</b>`;
						}else
						{
							numbers[n] = `<span class="receiver">${numbers[n]}</span>`;
							contacts[n] = `<span class="receiver">${contacts[n]}</span>`;
						}
					}
				}

				address.innerHTML = numbers.join("\n");
				contact_name.innerHTML = contacts.join("\n");
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
				option.text = `${num.split("~").join(", ")}: ${contactList[num]}`;
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

			document.getElementById("textsShown").innerHTML = c;
		}

		contactsSelect.addEventListener("change", function(e){
			let option = e.target.selectedOptions[0];

			updateCount(entryTable, filterTable(entryTable, option.dataset.address));
		});

		let contactList = getContactList(entryTable);

		updateTable(entryTable);
		updateContacts(contactList);
		updateCount(entryTable, undefined);
	]]>
	</script>
</body>
</html>
</xsl:template>
</xsl:stylesheet>
