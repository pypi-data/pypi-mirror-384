import shutil

shell_name = __name__.partition('.')[0]
shell_bin = shutil.which(shell_name)
