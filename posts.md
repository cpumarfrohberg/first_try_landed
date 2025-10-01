---
title: "Posts"
permalink: /posts/
---

<style>
.site-footer {
  display: none !important;
}
</style>

All blog posts organized chronologically.

{% for post in site.posts %}
  <article class="post-preview">
    <h2><a href="{{ post.url }}">{{ post.title }}</a></h2>
    <p class="post-meta">{{ post.date | date: "%B %d, %Y" }}</p>
    <p>{{ post.excerpt | strip_html | truncatewords: 50 }}</p>
  </article>
{% endfor %}
