import re


def patch_from_string(body: str, patch: str) -> str:
    for line in patch.splitlines():
        line = line.strip()
        if line != '' and not line[0] == '#':
            items = line.split(' =>')
            if len(items) == 1:
                pattern = items[0]
                replacement = ''
            else:
                pattern, replacement = items
            body, subs = re.subn(pattern.strip(), replacement.strip(), body)

            if subs == 0:
                print('Warning: replacement not applied:', line)

    return body


def patch_from_file(xml_body: str, patch_file: str, patch_write: bool) -> str:
    with open(patch_file) as f:
        patch_text = f.read()
        xml_body = patch_from_string(xml_body, patch_text)
    if patch_write:
        with open(patch_file + '.xml', 'w') as f:
            f.write(xml_body)

    return xml_body
