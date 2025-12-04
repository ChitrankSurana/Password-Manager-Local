# -*- coding: utf-8 -*-
"""
Test Suite for Personal Password Manager
=======================================

This module contains unit tests, integration tests, and security tests
for the Personal Password Manager application.

Test Categories:
- Unit Tests: Individual component testing
- Integration Tests: Component interaction testing
- Security Tests: Encryption, authentication, and access control
- Performance Tests: Load and response time testing
"""

import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
