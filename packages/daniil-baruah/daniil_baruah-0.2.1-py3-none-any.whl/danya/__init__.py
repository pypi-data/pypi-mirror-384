from pathlib import Path

from random import randint

class NotFile(Exception):
    '''
    Error if this object is not file.
    '''
    def __init__(self, filename):
        self.filename = filename

    def __str__(self):
        return f"This is not file: {self.filename}"
    

class NoFile(Exception):
    """
    Error if there is no file.
    """
    def __init__(self, filename):
        self.filename = filename

    def __str__(self):
        return f"There is no {self.filename}"


class NoCodePath(Exception):
    """
    Error if there is no 'code' in PATH.
    """
    def __init__(self):
        self.sentence = "There is no 'code' in PATH. Before downloading the VS code please mark 'ADD TO PATH' "

    def __str__(self):
        return self.sentence

def create_file_or_dir(filename):
    '''
    This function creates files or dirs
    '''
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
    """
    This function edits FILES
    """
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
    '''
    This function reads FILES
    '''
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

import subprocess
import time

def turn_vs_code(sec=0):
    """
    Turn on VS Code.
    Waits `sec` seconds and then launches VS Code.
    Works on any computer if 'code' is in PATH.
    """
    try:
        import shutil

        code = shutil.which("code")
        if code is None:
            raise NoCodePath()
        time.sleep(sec)
        subprocess.run([code])
    except Exception as e:
        print("Error:", e)


def turn_excel(sec=0):
    '''
    Turn on Microsoft Excel.
    Waits `sec` seconds and then launches Microsoft Excel.
    '''
    time.sleep(sec)
    try:
        subprocess.run(["start", "excel"], shell=True)

    except Exception as e:
        print('Error:', e)

def turn_word(sec=0):
    '''
    Turn on Microsoft Word.
    Waits `sec` seconds and then launches Microsoft Word.
    '''
    time.sleep(sec)
    try:
        subprocess.run(["start", "winword"], shell=True)

    except Exception as e:
        print('Error:', e)

def turn_powerpoint(sec=0):
    '''
    Turn on Microsoft PowerPoint.
    Waits `sec` seconds and then launches Microsoft PowerPoint.
    '''
    time.sleep(sec)
    try:
        subprocess.run(["start", "powerpnt"], shell=True)

    except Exception as e:
        print('Error:', e)


