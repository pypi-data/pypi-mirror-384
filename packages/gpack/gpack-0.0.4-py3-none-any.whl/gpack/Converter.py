def hex2binary(hex):
    slovar = {'0': '0000', '1': '0001', '2': '0010', '3': '0011','4': '0100', '5': '0101', '6': '0110', '7': '0111','8': '1000', '9': '1001', 'A': '1010', 'B': '1011','C': '1100', 'D': '1101', 'E': '1110', 'F': '1111','a': '1010', 'b': '1011', 'c': '1100', 'd': '1101','e': '1110', 'f': '1111'}
    binary_result = ''
    for i in hex:
        if i in slovar:
            binary_result += slovar[i]
        else:
            print(f"Недопустимый hex символ: {i}")
    return binary_result

def deciminal2binary(deciminal):
    try:
        deciminal = int(deciminal)
        if deciminal == 0:
            return "0"
        binary = ""
        num = deciminal
        while num > 0:
            binary = str(num % 2) + binary
            num = num // 2
        return binary
    except Exception as e:
        print(f"Недопустимый deciminal символ! Ошибка: {e}.")
        
def binary2deciminal(binary):
    try:
        binary = str(binary)
        if binary == "0":
            return 0
        deciminal = 0
        length = len(binary)
        for i in range(length):
            digit = int(binary[i])
            power = length - i - 1
            deciminal += digit * (2 ** power)
        return deciminal
    except Exception as e:
        print(f"Недопустимый binary символ! Ошибка: {e}.")

def binary2hex(binary):
    slovar = {'0000': '0', '0001': '1', '0010': '2', '0011': '3','0100': '4', '0101': '5', '0110': '6', '0111': '7','1000': '8', '1001': '9', '1010': 'A', '1011': 'B','1100': 'C', '1101': 'D', '1110': 'E', '1111': 'F'}
    hex_result = ''
    try:
        padding = (4 - len(binary) % 4) % 4
        if padding > 0:
            binary = '0' * padding + binary
        lenght = len(binary)/4
        for x in range(0,int(lenght)):
            xv = x*4
            i = binary[xv+0]+binary[xv+1]+binary[xv+2]+binary[xv+3]
            if i in slovar:
                hex_result += slovar[i]
            else:
                print(f"Недопустимый binary символ: {i}")
        return hex_result
    except Exception as e:
        print(f"Недопустимый binary символ! Ошибка: {e}.")

if __name__=='__main__':
    print('1 - Hex to Binary, 2 - Binary to Hex, 3 - Deciminal to Binary, 4 - Binary to Deciminal, 5 - Hex to Deciminal, 6 - Deciminal to Hex:')
    while True:
        mode = input('Mode: ')
        if mode=="1":
            print(f"Selected mode: {mode}")
            print(f"Hex2Binary: {hex2binary(input('Enter Hex: '))}")
        if mode=="2":
            print(f"Selected mode: {mode}")
            print(f"Binary2Hex: {binary2hex(input('Enter Binary: '))}")
        if mode=="3":
            print(f"Selected mode: {mode}")
            print(f"Deciminal2Binary: {deciminal2binary(input('Enter Deciminal: '))}")
        if mode=="4":
            print(f"Selected mode: {mode}")
            print(f"Binary2Deciminal: {binary2deciminal(input('Enter Binary: '))}")
        if mode=="5":
            print(f"Selected mode: {mode}")
            print(f"Hex2Deciminal: {binary2deciminal(hex2binary(input('Enter Hex: ')))}")
        if mode=="6":
            print(f"Selected mode: {mode}")
            print(f"Deciminal2Hex: {binary2hex(deciminal2binary(input('Enter Deciminal: ')))}")