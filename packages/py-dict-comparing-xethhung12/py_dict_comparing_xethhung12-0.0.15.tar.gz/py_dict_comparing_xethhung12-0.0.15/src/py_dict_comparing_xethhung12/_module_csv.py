
import csv
def load_win_based_CSV(path)->[dict]:
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter='|', quotechar='"')
        set_header=False
        lines = []
        for row in reader:
            lines.append(row)
        print(f"Complete loading the file[{path}]")
        return lines