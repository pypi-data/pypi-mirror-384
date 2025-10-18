# riddhulib/addcode.py
# Author: Riddhesh Wagvekar
# Description: A simple function that adds two numbers and prints the result.

def add_numbers(num1, num2):
    """
    Adds two numbers and prints their sum.

    Parameters:
        num1 (int or float): The first number.
        num2 (int or float): The second number.

    Returns:
        int or float: The sum of num1 and num2.

    Example:
        >>> add_numbers(10, 5)
        The sum is: 15
    """
    # Add the two numbers
    sum_result = num1 + num2

    # Print the result to the console
    print("The sum is:", sum_result)

    # Return the result in case it's needed later
    return sum_result
