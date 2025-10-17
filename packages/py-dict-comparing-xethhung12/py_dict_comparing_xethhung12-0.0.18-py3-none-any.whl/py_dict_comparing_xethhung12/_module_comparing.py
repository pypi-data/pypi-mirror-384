import os
import secrets
import csv
import json
import io
from dataclasses import dataclass, asdict, field
from itertools import combinations
from collections.abc import Callable
import hashlib
import tempfile
import copy

HASH_DELIMITER="___sssdfjs.xhsldfskjfjdsy___"

def hashing(data: str)->str:
    m = hashlib.sha256()
    m.update(data.encode('utf-8'))
    m.digest()
    return m.hexdigest()

def hash_with_separator(keys: [str])->str:
    keys.sort()
    return hashing(HASH_DELIMITER.join(keys))

@dataclass
class ComparingFileRecord():
    name: str

def view_only():
    """
    A decorator that checks a condition before allowing method execution.
    The condition_func should be a callable that takes the instance (self)
    as an argument and returns True if the condition is met, False otherwise.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            def condition_func(self):
                return self.is_view

            if condition_func(self):
                return func(self, *args, **kwargs)
            else:
                raise PermissionError("This method only available when working as view.")
        return wrapper
    return decorator

class ColumnPatching():
    pass

@dataclass
class ColumnRenamePatching(ColumnPatching):
    from_name: str
    to_name: str

@dataclass
class CompareData():
    data: [dict]
    name: str
    repo: 'ComparingRepo'
    headers: [str] = field(init=False)
    hashes: dict = field(init=False)
    indexing: dict = field(init=False)
    is_view: bool = False
    session: str = field(default=lambda: "")
    columnPatching: ColumnPatching = field(default_factory=lambda: [])
    

    def take_lines(self, lines: [int])->'Comparedata':
        self.__internal_reload()
        dd=[]
        convert = {}
        # for index, i in enumerate(lines):
        #     dd.append(self.data[i])
            # convert[index]=i
        convert = {index:i for index,i in enumerate(lines)}
        # view = self.as_view()
        # view.__indexing_lines(lambda x: convert[x])
        d = CompareData(dd, self.name, self.repo)
        # d.indexing_lines(lambda x: convert[x])
        d.indexing = convert
        self.__internal_clear()
        return d
    
    def as_view(self, columnPatchingList: [ColumnPatching] = []) -> 'Comparedata':
        self.__internal_reload()
        view = CompareData(copy.deepcopy(self.data), self.name, self.repo, is_view=True, columnPatching=columnPatchingList)
        self.__internal_clear()
        return view

    def __indexing_lines(self, indexing_algo:Callable[[int], str] = lambda x: x):
        indexing = {}
        for index, row in enumerate(self.data):
            indexing[index]= indexing_algo(index)
        self.indexing = indexing
    
    def indexing_lines(self, algo:Callable[[int], str] = lambda x: x):
        self.__indexing_lines(algo)

    def __internal_clear(self):
        self.data


    def __internal_reload(self):
        self.repo._reload_data(self)
        self.headers = [k for k in self.data[0]]
        self.headers.sort()
        if self.is_view:
            self.session = hashing(secrets.token_hex(16))
            for i in self.columnPatching:
                if isinstance(i, ColumnRenamePatching):
                    if i.from_name in self.headers:
                        self.headers.remove(i.from_name)
                        self.headers.append(i.to_name)
                        for item in self.data:
                            item[i.to_name] = item[i.from_name]
                            del item[i.from_name]
                else:
                    raise Exception("Unexpected column patching")
            self.headers.sort()
        self.__indexing_lines()

        data_hashes = []
        for index in range(1, len(self.headers)+1):
            for item in combinations(self.headers, index):
                data_hashes.append(item)
    
        data_hashes = [list(i) for i in data_hashes]
        for i in data_hashes:
            i.sort()

        hashed_dict = {}
        for i in data_hashes:
            k=hash_with_separator(i)
            hashed_dict[k] = i
        self.hashes = hashed_dict

    def __post_init__(self):
        self.__internal_reload()

        if self.is_view:
            self.repo.add_view(self)
        
        self.__internal_clear()

    
    def match_header(self, cd: 'CompareData'):
        self.__internal_reload()
        cd.__internal_reload()
        headers_other=cd.headers
        headers_our=self.headers
        other_only = []
        our = []
        our_only = []
        common = []
        for h in headers_other:
            if h not in headers_our:
                other_only.append(h)
            else:
                if h not in common:
                    common.append(h)
        
        for h in headers_our:
            if h not in headers_other:
                our_only.append(h)
            else:
                if h not in common:
                    common.append(h)
        self.__internal_clear()
        return our_only, common, other_only
    
    def data_hash_for_column(self, keys: [str])->dict:
        column_hash=hash_with_separator(keys)
        data_dict={}
        for index, d in enumerate(self.data):
            hd=hash_with_separator([ d[k]for k in self.hashes[column_hash]])
            if hd not in data_dict:
                data_dict[hd]=[]
            data_dict[hd].append(index)
        return data_dict
    
    def _get_hashed_data_paths(self, keys: [str], chunk_size: int = 20000) -> [str]:
        """
        Creates temporary JSON files with hashes and indices for the given keys,
        split into chunks. This is a memory-efficient alternative to
        data_hash_for_column for large datasets.
        """
        # column_hash = hash_with_separator(keys)
        # data_dict = {}
        # for index, d in enumerate(self.data):
        #     hd = hash_with_separator([str(d.get(k, '')) for k in self.hashes[column_hash]])
        #     if hd not in data_dict:
        #         data_dict[hd] = []
        #     data_dict[hd].append(index)

        # paths = []
        # items = list(data_dict.items())
        # for i in range(0, len(items), chunk_size):
        #     chunk = dict(items[i:i+chunk_size])
        #     temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8', newline='')
        #     json.dump(chunk, temp_file)
        #     temp_file.close()
        #     paths.append(temp_file.name)
        print("Loading column hash")
        column_hash = hash_with_separator(keys)
        data_dict = {}
        print("Start digest hash")
        for index, d in enumerate(self.data):
            hd = hash_with_separator([str(d.get(k, '')) for k in self.hashes[column_hash]])
            if hd not in data_dict:
                data_dict[hd] = []
            data_dict[hd].append(index)
        print(f"Completed digest hash, total {len(data_dict)} hashes")

        paths = []
        chunk = {}
        t_size=0
        p_index=0
        for key, indices in data_dict.items():
            chunk[key] = indices
            t_size+=1
            if t_size >= chunk_size:
                temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8', newline='')
                json.dump(chunk, temp_file)
                temp_file.close()
                paths.append(temp_file.name)
                print(f"Patched batch {p_index} with {t_size} items")
                chunk = {}
                p_index+=1
                t_size = 0
        
        if t_size > 0:
            temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8', newline='')
            json.dump(chunk, temp_file)
            temp_file.close()
            paths.append(temp_file.name)
            print(f"Patched the last batch of id {p_index} with {t_size} items")
            chunk = {}
            p_index+=1
            t_size = 0
        return paths

    def matching_keys(self, other: 'CompareData',keys: [str])->(int, int, [dict], [dict]):
        self.__internal_reload()
        column_hash=hash_with_separator(keys)
        hashes_our = self.hashes[column_hash]
        hashes_other = other.hashes[column_hash]

        our_hashes_paths = self._get_hashed_data_paths(hashes_our)
        self.__internal_clear()
        other.__internal_reload()
        other_hashes_paths = other._get_hashed_data_paths(hashes_other)
        other.__internal_clear
        
        all_temp_files = our_hashes_paths + other_hashes_paths
        found = []
        unfound = []

        try:
            our_batch_size=len(our_hashes_paths)
            other_batch_size=len(other_hashes_paths)
            print(f"{our_batch_size} batches to check over {other_batch_size} batches")
            for index_our, our_chunk_path in enumerate(our_hashes_paths):
                with open(our_chunk_path, 'r', encoding='utf-8') as f_our:
                    my_chunk_hash = json.load(f_our)
                
                for hash_id, our_indices in my_chunk_hash.items():
                    is_found_in_other = False
                    for other_chunk_path in other_hashes_paths:
                        with open(other_chunk_path, 'r', encoding='utf-8') as f_other:
                            other_chunk_hash = json.load(f_other)
                            if hash_id in other_chunk_hash:
                                found.append({"hash": hash_id, "our": our_indices, "other": other_chunk_hash[hash_id]})
                                is_found_in_other = True
                                break # Found in a chunk, no need to check other chunks for this hash_id
                    if not is_found_in_other:
                        unfound.append({"hash": hash_id, "our": our_indices})
                print(f"Completed {index_our+1}/{our_batch_size} batches check")
        finally:
            for temp_file_path in all_temp_files:
                os.unlink(temp_file_path)

        return sum([len(i['our']) for i in found]), sum([len(i['our']) for i in unfound]), found, unfound
    
    def original_index(self, lines: [int])->dict:
        original_index_dict = {}
        for i in lines:
            original_index = self.indexing[i]
            original_index_dict[i] = original_index
        return original_index_dict



class ComparingRepo():
    def __init__(self, temp_dir:str = ".temp-storage-for-comparing"):
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def __get_resource_path(self, name: str)->str:
        return f"{self.temp_dir}/.data.{name.replace("\\","/").replace("/","_")}"
    
    def __compare_data_as_meta_data(self, compare_data: CompareData)->dict:
        return asdict(d, dict_factory=lambda items: {k:v for k,v in items if k in ["data","session", "is_view", "columnPatching"]})

    def __default_meta_data(self, meta_data: [dict])->dict:
        return {"data": meta_data, "session": "", "is_view": False, "columnPatching": []}

    def load_data(self, name: str, data: [dict], force: bool = False)->CompareData:
        resource_path=self.__get_resource_path(name)
        self.__persist_meta_data(resource_path, self.__default_meta_data(data))
        d = CompareData(data,name,self)
        return d

    def load_data_from_generator(self, name: str, data: "Generator[dict, None, None]", force: bool = False)->CompareData:
        resource_path = self.__get_resource_path(name)
        meta_data_shell = self.__default_meta_data([])

        with open(resource_path, "w", encoding="utf-8") as f:
            f.write('{\n')
            for key, value in meta_data_shell.items():
                if key != 'data':
                    f.write(f'  "{key}": {json.dumps(value, ensure_ascii=False)},\n')
            
            f.write('  "data": [\n')
            first = True
            index=0
            for item in data:
                f.write(f'    {"" if first else ","}{json.dumps(item, ensure_ascii=False)}\n')
                index+=1
                if index % 10000 == 0:
                    print(f"Stored: {index} lines")
                first = False
            f.write('  ]\n}\n')

        d = CompareData([], name, self)
        return d
    
    def __persist_meta_data(self, path: str, meta_data: dict):
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(meta_data, ensure_ascii=False, indent=2))
    
    def add_view(self, data_record: CompareData):
        new_name = f"{data_record.name}_view_{data_record.session}"
        resource_path=self.__get_resource_path(new_name)
        self.__persist_meta_data(resource_path, self.__compare_data_as_meta_data(d))

    def _reload_data(self, compare_data: CompareData)->CompareData:
        resource_path=self.__get_resource_path(compare_data.name)
        with open(resource_path, "r", encoding="utf-8") as f:
            data = json.load(f) 

        compare_data.data = data["data"]
        compare_data.is_view = data["is_view"]
        compare_data.columnPatching = data["columnPatching"]
        compare_data.session = data["session"]
    

def compare():
    print("hello world")