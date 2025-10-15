from source_translator import SourceCode
from source_translator.langs import cpp, ts


language_names = {
    "py": "Python",
    "cpp": "C++",
    "ts": "TypeScript",
}


def code_to_samples(source):
    data = SourceCode(source)
    return {
        "ast": data.ast,
        "py": source,
        "cpp": cpp.CppTranslator().convert(data),
        "ts": ts.TypeScriptTranslator().convert(data),
    }
