#riddhuboss
#prct=1  Design a simple linear neural network model.
# Code:
# x=float(input("Enter value of x:"))
# w=float(input("Enter value of weight w:"))
# b=float(input("Enter value of bias b:"))
# net = int(w*x+b)
# if(net<0):
#   out=0
# elif((net>=0)&(net<=1)):
#   out =net
# else:
#   out=1
# print("net=",net)
# print("output=",out)


# 2 Calculate the output of neural net using both binary and bipolar sigmoidal function.

# Code:
# import numpy as np
# def sig(x):
#   return 1/(1 + np.exp(-x)) 
# x = 1.0
# print('Applying Sigmoid Activation on (%.1f) gives %.1f' % (x, sig(x)))
# x = -10.0
# print('Applying Sigmoid Activation on (%.1f) gives %.1f' % (x, sig(x)))
# x = 0.0
# print('Applying Sigmoid Activation on (%.1f) gives %.1f' % (x, sig(x)))
# x = 15.0
# print('Applying Sigmoid Activation on (%.1f) gives %.1f' % (x, sig(x)))
# x = -2.0
# print('Applying Sigmoid Activation on (%.1f) gives %.1f' % (x, sig(x)))


# # riddhulib/addcode.py
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
