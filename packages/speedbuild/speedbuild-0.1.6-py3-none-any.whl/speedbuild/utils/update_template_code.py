from ..src.Django.utils.feature_dependencies import getBlockDependencies
from ..src.Django.utils.var_utils import get_assigned_variables


def removeDecorator(code):
    blocks = code.split("\n")
    index = None

    for i in range(len(blocks)):
        if blocks[i].startswith("@"):
            index = i
        else:
            break
    
    if index != None:
        code_without_decorator = blocks[index:]
        return "\n".join(code_without_decorator).strip()
    
    return "\n".join(blocks).strip()


def addOrUpdateCode(current_code,new_code,old_code=None):

    if "import" in new_code:
        current_code.insert(0,new_code)
        return current_code
    
    var_name = []
    for block in current_code:
        code = removeDecorator(block)
        if not (code.startswith("import ") or code.startswith("from ")):
            var_name.append(get_assigned_variables(block))

    if old_code == None:        
        dependencies = getBlockDependencies(new_code,current_code)
        try:
            max_index = max([var_name.index(i['imports']) for i in dependencies if "imports " not in i and i['imports'] in var_name])
            
            if max_index + 1 > len(var_name):
                current_code.append(new_code)
            else:
                current_code.insert(max_index+1, new_code)

        except:
            current_code.append(new_code)
            
        
    else:
        # get old_code name
        name = get_assigned_variables(removeDecorator(old_code))
        index = var_name.index(name)
        current_code[index] = new_code
    
    return current_code


