def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


# Store functions inside a dictionary
operations = {
    "add": add,
    "subtract": subtract
}

# Retrieve a function
selected_function = operations["add"]

# Execute it
result = selected_function(10, 20)

print(result)