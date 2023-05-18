import re
import pandas as pd
import copy
import csv

class read_data:
    def __init__(self):
        pass
    def read_raw(self, file): 
        example = {}
        with open(file, 'r') as ex:
            while True:
                current_line = ex.readline().strip()
                # print(current_line)
                count_bit = 0
                for i in current_line:
                    count_bit+=1
                    if i == '\t':
                        break
                
                line = current_line[count_bit:]
                # print(line)
                if not line:
                    break
                all_line = re.split('-|,|/| ', line)
                tmp_line = []
                for i in range(len(all_line)):
                    new_line = ""
                    for each_alp in all_line[i]:
                        if ('a' <= each_alp <= 'z' or 'A' <= each_alp <= 'Z' or each_alp == ' ' or '0'<each_alp<'9') and each_alp != ' ':
                            new_line += each_alp.lower()

                    if new_line:
                        tmp_line.append([new_line])
                example[line] = {'processed': tmp_line}
        return example

    def read_return_raw(self, file):
        example = []
        with open(file, 'r') as ex:
            while True:
                current_line = ex.readline().strip()
                if not current_line:
                    break
                count_bit = 0
                for i in current_line:
                    count_bit+=1
                    if i == '\t':
                        break
                
                line = current_line[count_bit:]
                example.append(line)

        return example
    
    def read_uil_list(self):
        df = pd.read_excel('UIL.xlsx')
        data=df.values
        data2 = copy.deepcopy(df.values)
        for i in range(len(data)):
            str1 = ""
            str2 = ""
            str3 = ""
            str4 = ""
            str11 = ""
            str22 = ""
            str33 = ""
            str44 = ""
            for word1 in data[i][0]:
                str1 += word1.lower()
                str11 += word1
            data[i][0] = str1
            data2[i][0] = str11

            for word1 in data[i][1]:
                str2 += word1.lower()
                str22 += word1
            data[i][1] = str2
            data2[i][1] = str22

            for word1 in data[i][2]:
                str3 += word1.lower()
                str33 += word1
            data[i][2] = str3
            data2[i][2] = str33

            for word1 in data[i][4]:
                str4 += word1.lower()
                str44 += word1
            data[i][4] = str4
            data2[i][4] = str44

        # print(data2)
        return data, data2
    
    # def read_comp(self):
    #     df = pd.read_excel('human_match.xlsx', header=None)
    #     data=df.values
    #     # print(data[0][3])
    #     return data
    
    def read_his(self):
        result_dic = {}
        csv_reader = csv.reader(open('./modify.csv'))
        for line in csv_reader:
            result_dic[line[0]] = line[1]

        return result_dic
    
    def read_tmp_ct(self, file):
        result_dic = {}
        csv_reader = csv.reader(open(file))
        for line in csv_reader:
            result_dic[line[0]] = line[1]

        return result_dic