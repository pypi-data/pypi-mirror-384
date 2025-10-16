import re

varIdentifies = ["const","let","var"]

# TODO : handle single and multi line comment
chunk = """const getContacts= asyncHandler(async (req,res)=>{
    const hello = 1
    const contacts = await Contact.find({user_id:req.user._id})
    const name = hello
    res.status(200).json(contacts)
})"""

def removeCommentFromChunk(chunk):
    return chunk

# TODO : also collect variable name
def getLineValue(line):
    if "=" in line:
        pos = line.index("=") + 1
        return [line[:pos],line[pos:]]
    
    return None

# def getWordsInLine(line):
#     pass

def getWordsInLine(code, removeStrings=True):
    if code == None:
        return set()
    # Remove strings and comments
    if removeStrings:
        code = re.sub(r'(".*?"|".*?")', '', code)  # Remove strings
        
    code = re.sub(r'#.*', '', code)  # Remove comments
    
    # Extract words using regex (identifiers, keywords, function names, variable names)
    words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', code)
    
    return set(words)

def getChunkDependencies(chunk,chunks_name,raw_code=True,extra_deps=None):

    if raw_code: # TODO : investigate this 
        if chunk not in chunks_name.keys():
            print("getting ",chunk)
            print(chunks_name)
            raise ValueError("The code you want to parse is not in the file")
        
        chunk = chunks_name[chunk]

    deps = set(chunks_name)
    
    if extra_deps is not None:
        deps = deps.union(set(extra_deps))

    all_deps = set()
    exclude_deps = set()

    # remove comments from chunks
    chunk = removeCommentFromChunk(chunk)
    
    lines = chunk.split("\n")
    for line in lines:
        line = line.strip()
        line_word = line.split(" ")

        if line_word[0] in varIdentifies:

            line_diff = getLineValue(line)

            if line_diff is not None:
                # print(line_diff)
                beforeEqualSign,afterEqualSign = line_diff

                words_in_line = getWordsInLine(afterEqualSign)
                exclude_word = getWordsInLine(beforeEqualSign)

                chunk_dep = deps.intersection(words_in_line)
                
                exclude_deps= exclude_deps.union(exclude_word)
                # print(chunk_dep)
                all_deps = all_deps.union(chunk_dep)
        else:
            words_in_line = getWordsInLine(line)
            chunk_dep = deps.intersection(words_in_line)
            all_deps = all_deps.union(chunk_dep)


    if len(all_deps) > 0:
        # print(all_deps, " ", exclude_deps, " ", all_deps.difference(exclude_deps))
        return all_deps.difference(exclude_deps)
        
    return []
