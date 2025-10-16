import glob
import os


def _append_slash_if_dir(p):
    if p and os.path.isdir(p) and p[-1] != os.sep:
        return p + os.sep
    else:
        return p


def autocomplete_file_path(self, text, line, begidx, endidx):
    """File path autocompletion, used with the cmd module complete_* series functions"""
    # http://stackoverflow.com/questions/16826172/filename-tab-completion-in-cmd-cmd-of-python
    before_arg = line.rfind(' ', 0, begidx)
    if before_arg == -1:
        return  # arg not found

    fixed = line[before_arg + 1 : begidx]  # fixed portion of the arg
    arg = line[before_arg + 1 : endidx]
    pattern = arg + '*'

    completions = []
    for path in glob.glob(pattern):
        path = _append_slash_if_dir(path)
        completions.append(path.replace(fixed, '', 1))
    return completions
