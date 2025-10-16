import urllib.parse

def html_escaping_special_characters(word:str)->str:
    '''Description
    :return str: For example, if you enter "kx@jj5/g", it returns "kx%40jj5%2Fg"
    ### Escaping Special Characters such as @ signs in Passwords
    When constructing a fully formed URL string to pass to create_engine(), special characters such as those that may be used in the user and password need to be URL encoded to be parsed correctly.. This includes the @ sign.
    Below is an example of a URL that includes the password "kx@jj5/g", where the “at” sign and slash characters are represented as %40 and %2F, respectively:
    - https://docs.sqlalchemy.org/en/20/core/engines.html
    '''
    return urllib.parse.quote_plus(word)