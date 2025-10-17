import os
import secrets
import csv
import json
import io
from dataclasses import dataclass, asdict, field
from itertools import combinations
from collections.abc import Callable
import hashlib
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
    session: str = field(init=False)
    columnPatching: ColumnPatching = field(default_factory=list)
    

    def take_lines(self, lines: [int])->'Comparedata':
        index=0
        dd=[]
        convert = {}
        for i in lines:
            dd.append(self.data[i])
            convert[index]=i
            index+=1
        d = CompareData(dd, self.name, self.repo)
        d.indexing_lines(lambda x: convert[x])
        return d
    
    def as_view(self, columnPatchingList: [ColumnPatching] = []) -> 'Comparedata':
        view = CompareData(copy.deepcopy(self.data), self.name, self.repo, is_view=True, columnPatching=columnPatchingList)
        return view

    def __indexing_lines(self, indexing_algo:Callable[[int], str] = lambda x: x):
        indexing = {}
        for index, row in enumerate(self.data):
            indexing[index]= indexing_algo(index)
        self.indexing = indexing
    
    def indexing_lines(self, algo:Callable[[int], str] = lambda x: x):
        self.__indexing_lines(algo)

    def __post_init__(self):
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

        if self.is_view:
            self.repo.add_view(self)

    
    def match_header(self, cd: 'CompareData'):
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
    
    def matching_keys(self, other: 'CompareData',keys: [str])->(int, int, [dict], [dict]):
        column_hash=hash_with_separator(keys)
        hashes_our = self.hashes[column_hash]
        hashes_other = other.hashes[column_hash]

        found=[]
        unfound=[]
        other_data_hash = other.data_hash_for_column(hashes_other)
        my_data_hash = self.data_hash_for_column(hashes_our)

        for hash_id_for_mine in my_data_hash:
            if hash_id_for_mine in other_data_hash:
                found.append({"hash": hash_id_for_mine, "our": my_data_hash[hash_id_for_mine], "other": other_data_hash[hash_id_for_mine]})
            else:
                unfound.append({"hash": hash_id_for_mine, "our": my_data_hash[hash_id_for_mine]})
        return sum([1 for i in found for ii in i['our']]), sum([1 for i in unfound for ii in i['our']]), found, unfound
    
    def original_index(self, lines: [int])->dict:
        original_index_dict = {}
        for i in lines:
            original_index = self.indexing[i]
            original_index_dict[i] = original_index
        return original_index_dict



class ComparingRepo():
    def __init__(self, temp_dir:str = ".temp-storage-for-comparing"):
        self.temp_dir = temp_dir
        self.sys_registry = f"{self.temp_dir}/.sys-registry"
        os.makedirs(self.temp_dir, exist_ok=True)
        self.directory = {}
        self.__init_registy()
    
    def __get_resource_path(self, name: str)->str:
        return f"{self.temp_dir}/.data.{name.replace("\\","/").replace("/","_")}"

    def __get_digested_path(self, name: str)->str:
        return f"{self.temp_dir}/.digested.{name.replace("\\","/").replace("/","_")}"

    def ___update_digested_data(self, name: str, d: CompareData):
        p = self.__get_digested_path(name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(json.dumps(asdict(d, dict_factory=lambda items: {k:v for k,v in items if k not in ["repo", "name","session"]}),ensure_ascii=False, indent=2))


    def __init_registy(self):
        if not os.path.exists(self.sys_registry):
            self.___update_registry()
    
    def ___update_registry(self):
        with open(self.sys_registry, "w", encoding="utf-8") as f:
            f.write(json.dumps(self.directory,ensure_ascii=False, indent=2))
    
    def __update_root(self):
        self.___update_registry()

    def __update_data(self, name: str, d: CompareData):
        self.___update_digested_data(name, d)

    def load_data(self, name: str, data: [dict], force: bool = False)->CompareData:
        if name in self.directory and not force:
            raise Exception(f"CSV file[{name}] is not valid for register name[{name}]")
        resource_path=self.__get_resource_path(name)
        with open(resource_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))

        self.directory[name] = asdict(ComparingFileRecord(name))
        self.__update_root()

        d = CompareData(data,name,self)
        self.__update_data(name, d)
        return d
    
    def add_view(self, data_record: CompareData):
        new_name = f"{data_record.name}_view_{data_record.session}"
        resource_path=self.__get_resource_path(new_name)
        with open(resource_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
        self.directory[new_name] = asdict(ComparingFileRecord(new_name))
        self.__update_root()
        self.__update_data(new_name, data_record)


def compare():
    print("hello world")