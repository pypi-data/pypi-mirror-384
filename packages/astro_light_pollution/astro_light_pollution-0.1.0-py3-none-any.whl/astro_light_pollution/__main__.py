"""
Module that allows the package to be executed as a script.

This enables running the package with: python -m astro_light_pollution
"""
from .main import main

if __name__ == "__main__":
    main()