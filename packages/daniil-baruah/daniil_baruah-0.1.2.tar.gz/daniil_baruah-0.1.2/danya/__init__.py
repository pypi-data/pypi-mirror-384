from pathlib import Path

from random import randint

class NotFile(Exception):
    def __init__(self, filename):
        self.filename = filename

    def __str__(self):
        return f"This is not file: {self.filename}"
    

class NoFile(Exception):
    def __init__(self, filename):
        self.filename = filename

    def __str__(self):
        return f"There is no {self.filename}"
        

def create_file_or_dir(filename):
    path = Path(filename)

    if '.' in filename:
        if path.exists():
            print('You already have this file!')
        else:
            path.touch()
            print(f'New file has been created successfully! {filename}')
    else:
        if path.exists():
            print('You already have this directory!')
        else:
            path.mkdir()
            print(f'New directory has been created successfully! {filename}')


def edit_file(filename):
    path = Path(filename)

    if '.' not in filename:
        raise NotFile(filename)

    else:
        
        def write():
            while True:
                qty_of_str = input('Please enter the quantity of strings: ')
                try:
                    qty_of_str = int(qty_of_str)
                    break
                except ValueError:
                    print('❌ This is not a number, try again.')

            for _ in range(qty_of_str):
                prompts = [
                    'Please write your text: ',
                    'Enter your text: ',
                    "Don’t be slow, write faster! ",
                    "Don’t be shy, nobody will see this! ",
                    "Write down something! "
                ]
                text_for_input = prompts[randint(0, len(prompts) - 1)]
                text = input(text_for_input)
                with open(filename, 'a', encoding='utf-8') as file:
                    file.write(text + '\n')

            print('✅ All text was written successfully!')

        if not path.exists():
            create_file_or_dir(filename=filename)

        write()  


def read_file(filename):
    path = Path(filename)

    if '.' not in filename:
        raise NotFile(filename)
    
    else:
        
        def read():
            with open(filename) as file:
                print(f'Reading {filename}...')
                print()
                print(file.read())
                print()
                print('End of the file.')

        

        if not path.exists():
            create_file_or_dir(filename=filename)
            return

        read()

def delete_file(filename):
    '''
    You can easily delete files using this function.
    But if there is no file, there will be error.
    Please use try/except block!!!
    '''
    path = Path(filename)

    if not path.exists():
        raise NoFile(filename=filename)

    if '.' in filename:
        path.unlink()
        print(f'{filename} was successfully deleted!')
        return

    else:
        path.rmdir()
        print(f"{filename} was successfully deleted!")
        return
    
my_name = 'Daniil'