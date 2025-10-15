def get_ratio(num1, num2):
    """
    calculates the ratio between two numbers
    Args:
        num1: first number
        num2: second number
    Returns: 
        _: the ratio between the greater and lesser number (lesser/greater)
        state: a variable indicating which number is larger

    Dependencies: 
        None
    """

    if(num1 > num2):
        state = 1
        return ((num2/num1), state)

    elif(num2 > num1):
        state = 2
        return ( (num1/num2), state)

    else:
        return 0

def a_sum(input):
    """
    calculates the sum of an array
    Args:
        input: a one-dimensional array
    Returns: 
        sum: the sum of all values in the array

    Dependencies: 
        None
    """
    sum = 0
    for i in range (0, len(input)):
            sum += input[i]

    return sum

def a_mean(input):
    """
    calculates the mean of an array
    Args:
        input: a one-dimensional array
    Returns: 
        the mean of the one-dimensional array

    Dependencies: 
        None
    """
    return ( a_sum(input) / len(input) )