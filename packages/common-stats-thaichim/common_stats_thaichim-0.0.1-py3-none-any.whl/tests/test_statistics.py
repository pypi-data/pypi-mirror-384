import pytest
from common_stats.statistics import mean, median, mode, standard_deviation
from math import sqrt

def test_mean():
    """Test the mean calculation."""
    assert mean([1, 2, 3, 4, 5]) == 3.0
    assert mean([10, 20, 30]) == 20.0
    assert mean([-1, 0, 1]) == 0.0
    assert mean([1]) == 1.0
    assert mean([1.5, 2.5, 3.5]) == 2.5

def test_median():
    """Test the median calculation."""
    assert median([1, 2, 3, 4, 5]) == 3.0
    assert median([1, 2, 3, 4]) == 2.5
    assert median([5, 1, 3, 2, 4]) == 3.0
    assert median([2, 1]) == 1.5
    assert median([1, 2, 3, 4, 5, 6, 7, 8]) == 4.5

def test_mode():
    """Test the mode calculation."""
    assert mode([1, 2, 3, 3, 4]) == [3]
    assert mode([1, 1, 2, 2]) == [1, 2]
    assert mode([1, 2, 3]) == []
    assert mode([4, 4, 4, 5, 5, 5, 6]) == [4, 5]
    assert mode([1, 1, 1, 2, 2, 2, 3, 3]) == [1, 2]

def test_standard_deviation_population():
    """Test the standard deviation calculation (population)."""
    assert standard_deviation([1, 2, 3, 4, 5], sample=False) == pytest.approx(sqrt(2), rel=1e-9)
    assert standard_deviation([10, 20, 30], sample=False) == pytest.approx(8.16496580927726, rel=1e-9)
    assert standard_deviation([-1, 0, 1], sample=False) == pytest.approx(0.816496580927726, rel=1e-9)
    assert standard_deviation([1], sample=False) == pytest.approx(0.0, rel=1e-9)
    assert standard_deviation([1.5, 2.5, 3.5], sample=False) == pytest.approx(0.816496580927726)  

def test_standard_deviation_sample():
    assert standard_deviation([1, 2, 3, 4, 5], sample=True) == pytest.approx(sqrt(2.5), rel=1e-9)
    assert standard_deviation([10, 20, 30], sample=True) == pytest.approx(10.0, rel=1e-9)
    assert standard_deviation([-1, 0, 1], sample=True) == pytest.approx(sqrt(1), rel=1e-9)
    assert standard_deviation([1, 2], sample=True) == pytest.approx(0.7071067811865476, rel=1e-9)
    assert standard_deviation([1.5, 2.5, 3.5], sample=True) == pytest.approx(1.0, rel=1e-9)

def test_empty_data():
    """Test that ValueError is raised with empty data."""
    with pytest.raises(ValueError, match="The data list is empty"):
        mean([])
    with pytest.raises(ValueError, match="The data list is empty"):
        median([])
    with pytest.raises(ValueError, match="The data list is empty"):
        mode([])
    with pytest.raises(ValueError, match="The data list is empty"):
        standard_deviation([], sample=False)
    with pytest.raises(ValueError, match="The data list is empty"):
        standard_deviation([], sample=True)


def test_non_numeric_data():
    """Test that TypeError is raised with non-numeric data."""
    with pytest.raises(TypeError, match="All items in the data list must be numeric"):
        mean([1, 2, 'three'])
    with pytest.raises(TypeError, match="All items in the data list must be numeric"):
        median([1, 2, 'three'])
    with pytest.raises(TypeError, match="All items in the data list must be numeric"):
        mode([1, 2, 'three'])
    with pytest.raises(TypeError, match="All items in the data list must be numeric"):
        standard_deviation([1, 2, 'three'], sample=False)
    with pytest.raises(TypeError, match="All items in the data list must be numeric"):
        standard_deviation([1, 2, 'three'], sample=True)

def test_sample_standard_deviation_edge_case():
    """Test edge case for sample standard deviation with fewer than 2 data points."""
    with pytest.raises(ValueError, match="Sample standard deviation requires at least two data points"):
        standard_deviation([1], sample=True)

if __name__ == "__main__":
    pytest.main()