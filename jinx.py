#!/usr/bin/env python3
"""Backward-compatible entrypoint: prefer ``jinx`` console script after install."""

from jinx.cli import main

if __name__ == "__main__":
    main()
