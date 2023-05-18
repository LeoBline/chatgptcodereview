import warnings
import contextlib
import requests
from urllib3.exceptions import InsecureRequestWarning
from read_data import read_data
from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
import time
start_time = time.time()
import csv
class snomed:
    def __init__(self):
        self.name = ""
        self.url = "http://ontoserver:8080/fhir/ValueSet/$expand?url=http://snomed.info/sct?fhir_vs=refset/32570071000036102&count=10&filter="
        self.payload={}
        self.headers = {
            'Accept': 'application/fhir+json',
            'Content-Type': 'application/fhir+json'
        }

    def ct_search(self, name): 
        url = self.url + name
        old_merge_environment_settings = requests.Session.merge_environment_settings
        @contextlib.contextmanager
        def no_ssl_verification():
            opened_adapters = set()
            def merge_environment_settings(self, url, proxies, stream, verify, cert):
                opened_adapters.add(self.get_adapter(url))
                settings = old_merge_environment_settings(self, url, proxies, stream, verify, cert)
                settings['verify'] = False
                return settings
            requests.Session.merge_environment_settings = merge_environment_settings
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', InsecureRequestWarning)
                    yield
            finally:
                requests.Session.merge_environment_settings = old_merge_environment_settings
                for adapter in opened_adapters:
                    try:
                        adapter.close()
                    except:
                        pass
            
        with no_ssl_verification():
            response = requests.get(url)
            if "contains" in response.json()["expansion"].keys():
                return response.json()["expansion"]["contains"][0]['display']
            else:
                return "Not Find"

    def ct_string_process(self, pre_data):
        string_for_ct = ""
        for ct_i in pre_data:
            string_for_ct += ct_i[0]
            string_for_ct += " "
        self.name = string_for_ct[:-1]
        # print(self.)
        return self.ct_search(self.name)

# following for boost
# import sys
# file_name = sys.argv[1]

# ex = sys.argv[2]
# import pandas as pd
# read_raw = read_data()
# ct = snomed()
# raw = read_raw.read_raw(ex)
# count = 0
# final_result = {}
# for i in raw.keys():
#     count += 1
#     if count % size != rank:
#         continue
#     pre_data = raw[i]['processed']
#     final_result[i] = ct.ct_string_process(pre_data)

# final_result_to = comm.gather(final_result, root = 0)
# writing_result = []
# if rank == 0:
#     datas = []
#     for i in range(12):
#         for all_keys in final_result_to[i].keys():
#             tmp = {}
#             tmp['left'] = all_keys
#             tmp['right'] = final_result_to[i][all_keys]
#             writing_result.append(tmp)
    
#     name = file_name+'.csv'
#     with open(name,'w',encoding='utf8', newline='') as f: 
#         w = csv.writer(f) 
        
#         w.writerow(writing_result[0].keys()) 
#         for x in writing_result: 
#             w.writerow(x.values())
