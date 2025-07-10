num1 = int(input('Escolha um numero: '))
num2 = int(input('Escolha outro numero: '))

option = int(input('Escolha uma ação: '))

res = 0
if option == 1:
    res = num1+num2
elif option == 2:
    res = num1-num2
elif option == 3:
    res = num1*num2
elif option == 4:
    res = num1/num2

print(res)