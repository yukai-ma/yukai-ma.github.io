---
layout: academic
permalink: /publications/
title: Publications
description: Publications are listed in reverse chronological order. <br> <b>*</b> denotes equal contribution.
nav: true
nav_order: 1
---
<h1 class="publications-page-title">Publications</h1>
<p>{{ page.description }}</p>
<div class="publications">

{% bibliography -f {{ site.scholar.bibliography }} --template bib-academic %}

</div>
