from typing import List, Union
from collections import Counter
import math

def mean(data: List[Union[int, float]]) -> float:
    """
    Calculate the mean (average) of a list of numbers.

    Parameters:
    - data (List[Union[int, float]]): A list of numbers.

    Returns:
    - float: The mean of the numbers.

    Raises:
    - ValueError: If the input list is empty.
    - TypeError: If the input list contains non-numeric values.
    """
    if not data:
        raise ValueError("The data list is empty")
    if not all(isinstance(x, (int, float)) for x in data):
        raise TypeError("All items in the data list must be numeric")
    return sum(data) / len(data)

def median(data: List[Union[int, float]]) -> float:
    """
    Calculate the median of a list of numbers.

    Parameters:
    - data (List[Union[int, float]]): A list of numbers.

    Returns:
    - float: The median of the numbers.

    Raises:
    - ValueError: If the input list is empty.
    - TypeError: If the input list contains non-numeric values.
    """
    if not data:
        raise ValueError("The data list is empty")
    if not all(isinstance(x, (int, float)) for x in data):
        raise TypeError("All items in the data list must be numeric")
    sorted_data = sorted(data)
    n = len(sorted_data)
    mid = n // 2
    if n % 2 == 0:
        # For even number of data points, return the average of the two middle numbers
        return (sorted_data[mid - 1] + sorted_data[mid]) / 2
    else:
        # For odd number of data points, return the middle number
        return sorted_data[mid]


def mode(data: List[Union[int, float]]) -> List[float]:
    """
    Calculate the mode(s) of a list of numbers. The mode is the number(s) that appear most frequently.

    Parameters:
    - data (List[Union[int, float]]): A list of numbers.

    Returns:
    - List[float]: A list of the most frequent number(s). If all values are unique, returns an empty list.

    Raises:
    - ValueError: If the input list is empty.
    - TypeError: If the input list contains non-numeric values.
    """
    if not data:
        raise ValueError("The data list is empty")
    if not all(isinstance(x, (int, float)) for x in data):
        raise TypeError("All items in the data list must be numeric")
    
    frequency = Counter(data)
    max_freq = max(frequency.values())
    modes = [key for key, freq in frequency.items() if freq == max_freq]
    
    # If the highest frequency is 1 and all values are unique, return an empty list.
    return modes if max_freq > 1 else []


def standard_deviation(data: List[Union[int, float]], sample: bool = False) -> float:
    """
    Calculate the standard deviation of a list of numbers.

    Parameters:
    - data (List[Union[int, float]]): A list of numbers.
    - sample (bool): If True, calculate sample standard deviation. Otherwise, calculate population standard deviation.

    Returns:
    - float: The standard deviation of the numbers.

    Raises:
    - ValueError: If the input list is empty.
    - TypeError: If the input list contains non-numeric values.
    - ValueError: If the data list has fewer than 2 elements when calculating sample standard deviation.
    """
    if not data:
        raise ValueError("The data list is empty")
    if not all(isinstance(x, (int, float)) for x in data):
        raise TypeError("All items in the data list must be numeric")
    if len(data) < 2 and sample:
        raise ValueError("Sample standard deviation requires at least two data points")
    
    mu = mean(data)
    variance = sum((x - mu) ** 2 for x in data) / (len(data) - (1 if sample else 0))
    return math.sqrt(variance)
