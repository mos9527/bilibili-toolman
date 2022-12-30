'''Languages aren't created equally to begin with. And some just isn't liked...by Bilibili.

Sanitizers are attempts to address this issue. They work by replacing / translating
"illicit" words / phrases into "better, more suitable" forms.

A sanitizer function takes 
* 1 positional argument (string)
* any number of keyword arguments

And returns a tuple
* string to be matched by regex
* regex to be used 
* replacement strategey

... where a `replacement strategey` is a pure function.
* takes one string input
* give one string output

Sanitizers are constructed with `@sanitizer` wrapper. You'll find some examples in the code below.
'''
from functools import wraps
def sanitizer(function):
    @wraps(function)
    def wrapper(string,**kw):
        import re
        string, regex, replace_strategy = function(string, **kw)
        regex = re.compile(regex)
        index, output = 0, ''    
        for result in regex.finditer(string):
            begin,end = result.span()
            output += string[index:begin]
            output += replace_strategy(string[begin:end])
            index = end
        output += string[index:]
        return output
    return wrapper

def sanitizer_strategy_replace_with(char):
    '''Replaces forbidden characters with other one(s)'''
    def strategy(str):
        return char * len(str)
    return strategy

@sanitizer
def sanitize_korean(string,replace_with="█",replace_with_romaji=False):  
    '''Korean is banned by the site...huh

    Switches:
        replace_with_romaji (bool) : If True, `korean-romanizer` will be used to translate Hangul into romal forms. (Defaults to False).
        replace_with (str) : Replaces korean characters with something else (Defaults to █).
    '''    
    strategy = sanitizer_strategy_replace_with(replace_with)
    if replace_with_romaji:
        def korean_romanization(str):
            # Implements Korean romanization : https://github.com/osori/korean-romanizer
            from korean_romanizer.romanizer import Romanizer
            return Romanizer(str).romanize()
        strategy = korean_romanization
    return string, '[\uAC00-\uD7A3]+' , strategy
