# read_nav.py
def read_nav(filepath):
    data = []
    with open(filepath, "r") as file:
        for line in file:
            if "END OF HEADER" in line:
                break
        for line in file:
            data.append(line.strip())
    return data