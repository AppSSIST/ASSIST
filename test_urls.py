#!/usr/bin/env python
"""Test script to verify URL patterns are registered"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

from django.urls import get_resolver
from django.urls.exceptions import Resolver404

resolver = get_resolver()

# Test if /api/schedules/ is in the URL patterns
test_urls = [
    '/api/schedules/',
    '/api/faculty/1/',
    '/api/courses/1/edit/',
    '/api/rooms/1/',
    '/api/sections/1/',
    '/api/schedules/1/',
]

print("Testing URL patterns:\n")
for url in test_urls:
    try:
        match = resolver.resolve(url)
        print(f"✓ {url:30} -> {match.func.__name__}")
    except Resolver404:
        print(f"✗ {url:30} -> NOT FOUND")

print("\n\nDetailed URL mapping:\n")
for url in test_urls:
    try:
        match = resolver.resolve(url)
        print(f"{url:30} -> func: {match.func}")
        if hasattr(match.func, '__name__'):
            print(f"{' '*30}    name: {match.func.__name__}")
        if hasattr(match.func, 'cls'):
            print(f"{' '*30}    cls: {match.func.cls.__name__}")
    except Resolver404:
        pass
