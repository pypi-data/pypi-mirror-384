import re


# Extract imports
def extract_imports(lines):
    return [line for line in lines if line.startswith("from") or line.startswith("import")]

# Extract urlpatterns
def extract_urlpatterns(lines):
    in_urlpatterns = False
    urls = []
    for line in lines:
        if "urlpatterns" in line:
            in_urlpatterns = True
            continue

        if line.strip() == "]":
            break

        elif in_urlpatterns:
            if len(line.strip()) > 0:
                urls.append(line)

    return urls

# Extract router definitions and rename if necessary
def extract_router(lines, suffix):
    router_defs = {}
    router_lines = []
    router_pattern = re.compile(r"^(\w+)\s*=\s*(\w+Router)\(\)")  # Matches `router = RouterType()`

    for line in lines:
        match = router_pattern.match(line)
        if match:
            router_name, router_type = match.groups()
            new_router_name = f"{router_name}_{suffix}"  # Rename to avoid conflicts
            line = line.replace(router_name, new_router_name)
            router_defs[new_router_name] = router_type
            router_lines.append(line)

    return router_lines, router_defs

# Extract direct `urlpatterns += router.urls` usage and rename routers
def extract_router_urlpatterns(lines, router_dict):

    direct_router_urls = []
    register_url = []

    for line in lines:
        if not(line.startswith("import ") or line.startswith("from ")):
            for old_name, _ in router_dict.items():
                new_name = old_name
                old_name = old_name.split("_")
                old_name.pop()
                old_name = "_".join(old_name)

                if old_name in line:
                    if "urlpatterns" in line:
                        delimeter = "="
                        if "+=" in line:
                            delimeter = "+="

                        code = line.split(delimeter)[1].strip().replace(old_name,new_name)

                        register_url.append(code)
                    else:
                        try:
                            if line.split("=")[1].strip().startswith(_):
                                continue
                        except ValueError:
                            pass

                        direct_router_urls.append(line.replace(old_name,new_name))

    return [direct_router_urls,register_url]


def merge_urls(urls1,urls2):

    imports1 = extract_imports(urls1)
    imports2 = extract_imports(urls2)

    # Merge imports without duplicates
    merged_imports = sorted(set(imports1 + imports2))

    urlpatterns1 = extract_urlpatterns(urls1)
    urlpatterns2 = extract_urlpatterns(urls2)

    merge_patterns = sorted(set(urlpatterns1+urlpatterns2))

    # Merge urlpatterns while ensuring all unique paths are included
    patterns = ["urlpatterns = [","\n"]
    patterns.extend(merge_patterns)
    patterns.extend("]")

    router_lines1, router_defs1 = extract_router(urls1, "1")
    router_lines2, router_defs2 = extract_router(urls2, "2")

    # Merge routers while preserving different router names
    merged_router_code = sorted(set(router_lines1 + router_lines2))

    router_urlpatterns1, register_rounter1_urls = extract_router_urlpatterns(urls1, router_defs1)
    router_urlpatterns2, register_rounter2_urls = extract_router_urlpatterns(urls2, router_defs2)

    # Merge router urlpatterns without duplication
    merged_router_urlpatterns = sorted(set(router_urlpatterns1 + router_urlpatterns2))
    merged_router_code += merged_router_urlpatterns

    # merge register_router_urls
    merge_register_router = sorted(set(register_rounter1_urls + register_rounter2_urls))

    # Ensure `include(router.urls)` is only added once
    if any("include(" in line for line in patterns) and merged_router_urlpatterns:
        merged_router_urlpatterns = []  # Avoid duplicate API URL inclusion


    url_code = merged_imports + ["\n"] + merged_router_code + ["\n\n"]

    url_code = [i for i in url_code if len(i.strip()) > 0]

    code = "\n".join(url_code) + "\n\n\n"

    url_code = patterns + [f" + {route}" for route in merge_register_router]
    url_code = [i for i in url_code if len(i.strip()) > 0]
    code += "\n".join(url_code)

    return code