from django.contrib import sitemaps
from django.urls import reverse


class Sitemap(sitemaps.Sitemap):
    def items(self):
        return [
            {'name': 'quotes:home', 'args': [], 'pri': '1.0'},
            {'name': 'quotes:plans', 'args': [], 'pri': '0.7'},
        ]

    def location(self, item):
        return reverse(item['name'], args=item['args'])

    def priority(self, item):
        return item['pri']

    def changefreq(self, item):
        return "weekly"