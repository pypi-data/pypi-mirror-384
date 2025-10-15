#!/usr/bin/env python3
"""
Test script for hello_team package with colorama
"""

from hello_team import hello_team

print("=" * 60)
print("🎨 Testing hello_team Package with Colorama Colors")
print("=" * 60)

print("\n📝 Basic Usage (default green):")
hello_team()

print("\n🎨 Different Colors:")
hello_team("Python", "blue")
hello_team("JavaScript", "yellow")
hello_team("Ruby", "red")
hello_team("Go", "cyan")
hello_team("Rust", "magenta")

print("\n✨ Using Styles:")
hello_team("Backend", "green", "bright")
hello_team("Frontend", "blue", "bright")
hello_team("DevOps", "cyan", "dim")
hello_team("QA", "yellow", "normal")

print("\n🚀 Mixed Examples:")
hello_team("Security", "red", "bright")
hello_team("Data Science", "magenta", "bright")
hello_team("Mobile", "blue", "dim")

print("\n" + "=" * 60)
print("✅ All tests completed!")
print("=" * 60)
