import asyncio

from .src.Express.extract.reverseImport import convertToImportStatements
from .parsers.javascript_typescript.jsParser import JsTxParser


parser = JsTxParser()

#     print("Parsing Test.js")
imports, chunks, chunks_name, import_deps = asyncio.run(parser.parse_code("/home/attah/Documents/sb_final/speedbuild/test.js"))
print(import_deps)

o=convertToImportStatements(import_deps)

print(o)