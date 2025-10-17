
import csv
from typing import Generator, List

def load_win_based_CSV(path) -> List[dict]:
    with open(path, "r", encoding="utf-8-sig") as f:
        return list(load_win_based_CSV_generator(path))
        # reader = csv.DictReader(f, delimiter='|', quotechar='"')
        # lines = []
        # for row in reader:
        #     lines.append(row)
        # print(f"Complete loading the file[{path}]")
        # return lines

def load_win_based_CSV_generator(path) -> Generator[dict, None, None]:
    index=0
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter='|', quotechar='"')
        for row in reader:
            index+=1
            if index % 10000 == 0:
                print(f"Processed: {index} lines")
            yield row

    print(f"Complete loading the file[{path}]")