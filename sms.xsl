<?xml version="1.0" encoding="ISO-8859-1"?>
<!--
	~ Copyright (c) 2010 - 2016 Carbonite. All Rights Reserved.
	-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
								xmlns:msxsl="urn:schemas-microsoft-com:xslt"
								xmlns:user="http://android.riteshsahu.com">
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

		p {
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

			padding: 8px 12px;
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

			<tr data-address="{@address}" data-contact_name="{@contact_name}" data-type="{$typeStr}">
				<td><xsl:value-of select="$typeStr"/></td>
				<td><xsl:value-of select="@address"/></td>
				<td><xsl:value-of select="@contact_name"/></td>
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

		function updateCount(tbl)
		{
			document.getElementById("textsShown").innerHTML = tbl.rows.length - 1;
		}

		let contactList = getContactList(entryTable);

		updateCount(entryTable);
	]]>
	</script>
</body>
</html>
</xsl:template>
</xsl:stylesheet>
