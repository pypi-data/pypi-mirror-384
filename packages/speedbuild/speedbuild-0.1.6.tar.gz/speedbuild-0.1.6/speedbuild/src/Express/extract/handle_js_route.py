stringIdentifier = ["'",'"',"`"]
route_identifies = ["route","get","post","put","delete","use"] # and others

def getFirstParameter(code):
    og = code
    opening = ["(","[","{"]
    close = [")","]","}"]
    stack = ["("] # add the starting parantesis to stack
    code = code[1:] # ignore the leading opening paranthesis
    parameter = ""

    for char in code:
        if len(stack) == 0:
            break 

        if char in opening:
            stack.append(char)

        elif char in close:
            if len(stack) > 0:
                last_in_stack = stack[-1]
                if last_in_stack in opening and opening.index(last_in_stack) == close.index(char):
                    stack.pop(-1) # remove last character in stack

        elif char == ",":
            stack.pop() # remove opening bracket from stack
            break

        else:
            parameter += char

    if len(stack) > 0:
        raise ValueError("You have a synthax error in your code ")
    
    return parameter

def manageIdentifier(indentifier, code):
    code = code.split(f".{indentifier}")
    if len(code) == 0:
        return None
    
    code = code[1]

    try:
        return getFirstParameter(code)
    except ValueError as error:
        print("Error : ",error)
        return None

def getRoutePathAndMethodsOrReturnNone(code,chunks):
    """
    Extracts route path and HTTP methods from Express.js-like route definitions.

    This function analyzes code chunks to identify route paths and their associated HTTP methods
    in Express.js-style route definitions.

    Args:
        code (str): The line of code to analyze
        chunks (list): Additional code chunks (currently unused)

    Returns:
        list or None: A list containing [path_name, methods_list] if a valid route is found,
                     where path_name is the cleaned route path (str) and methods_list contains
                     the HTTP methods (list of str). Returns None if no valid route is found
                     or if the line starts with '/'.

    Example:
        >>> code = "app.get('/users', handler)"
        >>> getRoutePathAndMethodsOrReturnNone(code, [])
        ['/users', ['get']]
    """
    pathName = None
    methods = []

    if code.startswith("/"):
        return None #Dont process comments

    for indentifier in route_identifies:
        if f".{indentifier}(" in code:
            if indentifier != "route":
                methods.append(indentifier)

            path = manageIdentifier(indentifier,code)
            if path is not None:
                if path[0] in stringIdentifier and path[-1] in stringIdentifier:
                    pathName = path

    if pathName is not None:
        # print(f"Path : {pathName} , methods : {methods} ",code )
        return [pathName.replace("'","").replace('"',""),methods] #TODO : change later
    
