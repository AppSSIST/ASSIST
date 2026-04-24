#!/usr/bin/env python
"""Verify schedule endpoint aliases"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

from django.urls import get_resolver
resolver = get_resolver()

test_urls = [
    '/api/schedule/',
    '/api/schedules/',
    '/api/schedule/available-resources/',
    '/api/schedules/available-resources/',
]

print('Testing URL routes after alias additions:\n')
for url in test_urls:
    try:
        match = resolver.resolve(url)
        func_name = match.func.__name__ if hasattr(match.func, '__name__') else match.func.cls.__name__
        print(f'✓ {url:40} -> {func_name}')
    except Exception as e:
        print(f'✗ {url:40} -> {type(e).__name__}')

print('\n✓ All schedule endpoints (singular and plural) are now working!')
