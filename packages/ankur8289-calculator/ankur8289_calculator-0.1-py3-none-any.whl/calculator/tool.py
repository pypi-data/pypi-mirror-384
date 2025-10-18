import sys
def add(a, b):
    print("Within the add function!")
    return a + b

def main():
    if len(sys.argv) != 3:
        print(f"Provide 2 digits. Provided - {sys.argv[1:]}")
    else:
        num1 = int(sys.argv[1])
        num2 = int(sys.argv[2])
        print(f"The sum of the two numbers are: {add(num1, num2)}")

