---
title: "Categories"
permalink: /categories/
---

<style>
.site-footer {
  display: none !important;
}
</style>

Posts organized by category.

{% for category in site.categories %}
  <h2>{{ category[0] }}</h2>
  <ul>
    {% for post in category[1] %}
      <li><a href="{{ post.url }}">{{ post.title }}</a> - {{ post.date | date: "%B %d, %Y" }}</li>
    {% endfor %}
  </ul>
{% endfor %}
