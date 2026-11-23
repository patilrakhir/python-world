#
# ### Exercise 2: Reading a file safely
# Write `read_text_file(path)` that returns the file's text, or `None` if something goes wrong. Handle these separately with clear messages:
# - File doesn't exist.
# - No permission to read it.
# - File isn't valid UTF-8.
#
# Test with: a real file, a path that doesn't exist, and a folder path (what exception do you get?).


def read_text_file(path):

    try:
        with open(path, "r", encoding='utf-8') as file:
            content =file.read()
            return content

    except FileNotFoundError:
        print("File not found")
        return None

    except UnicodeDecodeError:
        print("File not a utf-8 encoded file")
        return None

    except PermissionError:
        print("Permission denied")
        return None

result = read_text_file ('sample.txt') #file path should be same as .py file
#C:\Users\Rakhi Ramdas Patil\PycharmProjects\prod_support_practice\sample.txt
print(result)

print (read_text_file ('sample.txt'))
