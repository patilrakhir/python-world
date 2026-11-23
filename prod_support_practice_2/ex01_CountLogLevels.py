
def count_levels(path):

    counts = {
        "INFO": 0,
        "WARN": 0,
        "ERROR": 0,
        "unparsed": 0
    }

    with open(path, "r", encoding="utf-8") as file:

        for line in file:

            parts = line.split()

            # Check whether the line has enough fields
            if len(parts) < 3:
                counts["unparsed"] += 1
                continue

            # Level is the third word in our log format
            level = parts[2]

            if level in counts and level != "unparsed":
                counts[level] += 1
            else:
                counts["unparsed"] += 1

    return counts


result = count_levels("./sample_data/app.log")
print(result)
