with open("gui_app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# line 2044 is 0-indexed index 2043.
# line 2534 is 0-indexed index 2533.
# Deleting lines[2043:2534] clears out lines 2044 to 2534.
del lines[2043:2534]

with open("gui_app.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Cleared out legacy business suite block successfully!")
