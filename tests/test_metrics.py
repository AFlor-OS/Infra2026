import pytest
from analysis.metrics import speedup, efficiency

def test_speedup():
    assert speedup(10.0, 5.0) == 2.0

def test_efficiency():
    assert efficiency(4.0, 4) == 1.0

def test_invalid_time():
    with pytest.raises(ValueError):
        speedup(10.0, 0.0)
