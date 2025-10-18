# Day 1
def n_input(n):
    """
    Take n integers as input from the user and return them as a list.
    
    Args:
        n (int): Number of integers to input
        
    Returns:
        list: List of n integers entered by user
    """
    numbers = []
    for i in range(1, n + 1):
        while True:
            try:
                value = int(input(f"Enter integer {i}: "))
                numbers.append(value)
                break
            except ValueError:
                print("Invalid input. Please enter an integer.")
    return numbers

# Day 2

def counter(lst):
    """
    Count occurrences of each item in a list.
    
    Args:
        lst (list): Input list
        
    Returns:
        dict: Dictionary with items as keys and their counts as values
        
    Example:
        >>> counter([1, 2, 3, 1, 2, 1])
        {1: 3, 2: 2, 3: 1}
    """
    item_count = {}
    for item in lst:
        if item in item_count:
            item_count[item] += 1
        else:
            item_count[item] = 1
    return item_count