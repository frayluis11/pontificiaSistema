"""
Debug URLs management command
"""
from django.core.management.base import BaseCommand
from django.urls import get_resolver

class Command(BaseCommand):
    help = 'Debug URL patterns'

    def handle(self, *args, **options):
        resolver = get_resolver()
        self.stdout.write("URL Patterns:")
        for pattern in resolver.url_patterns:
            self.stdout.write(f"  {pattern}")
            if hasattr(pattern, 'url_patterns'):
                for subpattern in pattern.url_patterns:
                    self.stdout.write(f"    {subpattern}")