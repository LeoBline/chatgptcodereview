import os
import uuid
from read_data import read_data
from snomed_ct import snomed
def snomed_ct_dict(exa):
    read_raw = read_data()
    ct = snomed()
    raw = read_raw.read_raw(exa)
    # count = 0
    final_result = {}
    for i in raw.keys():
        # count += 1
        # if count % size != rank:
        #     continue
        pre_data = raw[i]['processed']
        final_result[i] = ct.ct_string_process(pre_data)


    return final_result

    # following for boost
    # myuuid = uuid.uuid4()
    # cmd = 'mpiexec -n 12 python snomed_ct.py ' + str(myuuid) + ' ' + str(exa)
    # os.system(cmd)
    # file_name = str(myuuid)+ '.csv'
    
    # read = read_data()
    # result = read.read_tmp_ct(file_name)
    # # print(result)

    # os.remove(str(myuuid)+ '.csv')
    # return result


