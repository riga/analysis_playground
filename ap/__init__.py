# coding: utf-8

"""
Main entry point for top-level settings and fixes before anything else is imported.
"""

import law

law.contrib.load("arc", "cms", "numpy", "telegram", "root", "tasks", "wlcg")
