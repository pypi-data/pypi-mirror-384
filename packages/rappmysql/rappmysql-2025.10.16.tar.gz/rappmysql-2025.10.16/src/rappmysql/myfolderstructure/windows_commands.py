import subprocess

# pth2ps1skript =
# cmd = ['powershell', r"D:\powershell_skripts\folder_size.ps1"]
cmd = ['powershell', 'tree /f > tree.txt']
p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

out, err = p.communicate()

if p.returncode != 0:
    print('err', err)
else:
    print('out', out)