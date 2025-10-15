<?xml version='1.0' encoding='utf-8' ?>

<!--
  Copyright (C) 2024, 2025 Jaromir Hradilek

  A custom XSLT stylesheet  to convert a generic DITA topic  generated with
  the  asciidoctor-dita-topic[1] plug-in  to a  specialized  DITA  concept.
  The stylesheet expects  that the original AsciiDoc file  has followed the
  guidelines for  concept modules  as defined  in the Modular Documentation
  Reference Guide[2].

  Usage: xsltproc ––novalid concept-generated.xsl YOUR_TOPIC.dita

  [1] https://github.com/jhradilek/asciidoctor-dita-topic
  [2] https://redhat-documentation.github.io/modular-docs/

  MIT License

  Permission  is hereby granted,  free of charge,  to any person  obtaining
  a copy of  this software  and associated documentation files  (the "Soft-
  ware"),  to deal in the Software  without restriction,  including without
  limitation the rights to use,  copy, modify, merge,  publish, distribute,
  sublicense, and/or sell copies of the Software,  and to permit persons to
  whom the Software is furnished to do so,  subject to the following condi-
  tions:

  The above copyright notice  and this permission notice  shall be included
  in all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS",  WITHOUT WARRANTY OF ANY KIND,  EXPRESS
  OR IMPLIED,  INCLUDING BUT NOT LIMITED TO  THE WARRANTIES OF MERCHANTABI-
  LITY,  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT
  SHALL THE AUTHORS OR COPYRIGHT HOLDERS  BE LIABLE FOR ANY CLAIM,  DAMAGES
  OR OTHER LIABILITY,  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
  ARISING FROM,  OUT OF OR IN CONNECTION WITH  THE SOFTWARE  OR  THE USE OR
  OTHER DEALINGS IN THE SOFTWARE.
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <!-- Compose the XML and DOCTYPE declarations: -->
  <xsl:output encoding="utf-8" method="xml" doctype-system="concept.dtd" doctype-public="-//OASIS//DTD DITA Concept//EN" />

  <!-- Format the XML output: -->
  <xsl:output indent="yes" />
  <xsl:strip-space elements="*" />
  <xsl:preserve-space elements="codeblock pre screen" />

  <!-- Report an error if the converted file is not a DITA topic: -->
  <xsl:template match="/*[not(self::topic)]">
    <xsl:message terminate="yes">ERROR: Not a DITA topic</xsl:message>
  </xsl:template>

  <!-- Remove the outputclass attribute from the root element: -->
  <xsl:template match="/topic/@outputclass" />

  <!-- Prevent duplication of the abstract paragraph (used for shortdesc): -->
  <xsl:template match="//body/p[1][@outputclass='abstract']" />

  <!-- Perform identity transformation: -->
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()" />
    </xsl:copy>
  </xsl:template>

  <!-- Transform the root element: -->
  <xsl:template match="/topic">
    <xsl:element name="concept">
      <xsl:apply-templates select="@*|node()" />
    </xsl:element>
  </xsl:template>

  <!-- Transform the section element: -->
  <xsl:template match="//section">
    <xsl:element name="section">
      <xsl:apply-templates select="@*|*[not(self::p[@outputclass='title'][b='Additional resources'] or preceding-sibling::p[@outputclass='title'][b='Additional resources'])]" />
    </xsl:element>
  </xsl:template>

  <!-- Remove the Additional resources section (used for related-links): -->
  <xsl:template match="//section[title='Additional resources']" />

  <!-- Issue a warning if the converted file contains a nested section: -->
  <xsl:template match="//section/section">
    <xsl:message terminate="no">WARNING: Nested sections not allowed in DITA, skipping...</xsl:message>
  </xsl:template>

  <!-- Transform the body element: -->
  <xsl:template match="body">
    <!-- Compose the shortdesc element: -->
    <xsl:call-template name="shortdesc">
      <xsl:with-param name="contents" select="p[1][@outputclass='abstract']" />
    </xsl:call-template>
    <!-- Compose the conbody element: -->
    <xsl:element name="conbody">
      <xsl:apply-templates select="@*|*[not(self::p[@outputclass='title'][b='Additional resources'] or preceding-sibling::p[@outputclass='title'][b='Additional resources'])]" />
    </xsl:element>
    <!-- Compose the related-links element: -->
    <xsl:call-template name="related-links">
      <xsl:with-param name="contents" select="//p[@outputclass='title'][b='Additional resources']/following-sibling::*|//section[title='Additional resources']/*[not(self::title)]" />
    </xsl:call-template>
  </xsl:template>

  <!-- Include the common templates: -->
  <xsl:include href="common-templates.xsl" />

</xsl:stylesheet>
