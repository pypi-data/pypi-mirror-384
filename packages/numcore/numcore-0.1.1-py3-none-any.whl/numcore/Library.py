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