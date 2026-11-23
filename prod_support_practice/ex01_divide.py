# In Python, you define a function using the def keyword.

def devide_strings(a_text, b_text):
 try:
    a = int(a_text)
    b = int(b_text)
    result = a/b

 except ValueError:
    print ("Input isn't number")
    return None

 except ZeroDivisionError:
    print ("Divide By Zero")
    return None

 else:
     return result

 finally:
    print ("Finished Attempt")

print(devide_strings(10,2))
print(devide_strings('abc',2))
print(devide_strings(10,0))
