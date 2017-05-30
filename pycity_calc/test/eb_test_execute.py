#!/usr/bin/env python
# coding=utf-8
"""
Script to execute energy balance test with pytest. Not called within
all_test_execute.py due to erroneous behavior within test call.
"""

import pytest

#  Second, call energy balance tests
pytest.main(['test_simulation_energy_balances.py'])