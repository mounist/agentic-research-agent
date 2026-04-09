"""
data — Data access layer.

Provides a unified interface for both live WRDS and mock data modes.
Tool implementations call data layer functions rather than issuing
SQL directly, so swapping between live/mock is a single config toggle.
"""
