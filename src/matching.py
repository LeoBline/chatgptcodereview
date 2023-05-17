from read_data import read_data
from writing import writing
from collections import Counter
import spacy
import re
# from ct_test import snomed_ct_dict
from ct_test import snomed_ct_dict
from autoModel import autoModel
import editdistance
import MedicalDataClassifier as mdc
from MedicalDataClassifier.med_data_cls import train_nb_classifier, predict_medical_text
import copy

class map_sys:
    def __init__(self, file_name, write_file_name):
        # inital tmp name
        self.file = file_name
        self.reading = read_data()
        self.writing = writing()
        self.raw_plain = self.reading.read_raw(file_name)
        self.uil_list, self.uil_list_origan = self.reading.read_uil_list()
        self.result_mapping = []
        self.Non_process_text = self.reading.read_return_raw(file_name)
        self.raw_text_counter = 0
        self.classifier, self.text_vectorizer = train_nb_classifier()
        
        # inital tmp dictionary or function
        self.target = ""
        self.nlp = spacy.load("en_ner_bionlp13cg_md")
        self.parent = ""
        self.write_file_name = write_file_name
        self.mod_dict = self.reading.read_his()
        self.statement_check = False
        self.check_ct = False
        self.ct_find = False
        self.result_dict = {}
        self.ct_available_check = False
        self.new_dict_incl_distance = []

        # ct
        # self.uid = uid
        
    def mapping(self):
        # call snomed ct
        # ct_result = snomed_ct_dict(self.file)
        ct_result = snomed_ct_dict(self.file)
        
        # line id
        finding_id = 0
        
        # starting mapping
        for finding in self.raw_plain.keys():

            # setting as default
            self.result_dict = []
            finding_id += 1
            self.statement_check = False
            self.check_ct = False
            pre_data = self.raw_plain[finding]['processed']
            self.result_dict = {}
            self.target = ""
            self.ct_find = False
            self.ct_available_check = False

            left_mapping_text = self.Non_process_text[self.raw_text_counter]
            curr_ct = ct_result[left_mapping_text]
            self.raw_text_counter += 1
            self.spacy_pos(left_mapping_text)             
            result = ""
            basic_length = 2
            tmp_parent = ""

            word_check = self.medical_word_check(self.re_organ(pre_data))
            # print(word_check)
            
            for simgle_word in self.parent:
                tmp_parent += simgle_word.lower()

            # print(curr_ct)
            if curr_ct != "Not Find":
                self.ct_find = True
                self.ct_search(curr_ct)
                if self.result_dict:
                    for rr in self.result_dict.keys():
                        # self.result_mapping.append([left_mapping_text, rr, "SNOMED CT"])
                        self.check_ct = True
                        break
            
            # modify is the highest level
            if finding in self.mod_dict.keys():
                self.result_mapping.append([left_mapping_text, self.mod_dict[finding], 0, "UIL"]) 
                if self.ct_find: 
                    re_cover_text = self.re_organ(pre_data)
                    tmp_distance = self.quick_edit_distance(re_cover_text, curr_ct)               
                    self.new_dict_incl_distance.append([left_mapping_text, self.mod_dict[finding], 0, [],[tmp_distance],[], [curr_ct], "UIL", ""])
                else:
                    self.new_dict_incl_distance.append([left_mapping_text, self.mod_dict[finding], 0, [],[],[], [], "UIL", ""])
            else:
                self.parent = tmp_parent
                if self.ct_find:
                    self.find_parent(curr_ct)
                else:
                    self.find_parent(self.parent)
                # tmp_string_left = ""
                # combine searach
                if len(pre_data) >= 2:
                    for i in range(len(pre_data)):
                        if i + basic_length <= len(pre_data):
                            tmp_finding = pre_data[i:i+basic_length]
                            tmp_string = ""
                            for each_in_combine in tmp_finding:
                                tmp_string += str(each_in_combine[0])
                                tmp_string += " "
                            self.find_comb(tmp_string[:-1])

                # if finding in SNMONED CT
                if self.ct_find:
                    for ct_tmp in re.split(' ', curr_ct):
                        tmp_low = ""
                        for i_low in ct_tmp:
                            tmp_low += i_low.lower()
                        self.target=tmp_low
                        # print(self.target)
                        self.search(2)
                else:
                    for target in pre_data:
                        # print(target)
                        self.target = target[0]
                        self.search(1)

                candid_result_in_condition = []
                # being search in some place
                if self.statement_check:
                    re_cover_text = self.re_organ(pre_data)
                    if len(self.result_dict) > 0:
                        for find_key_in_condition in self.result_dict.keys():
                            candid_result_in_condition.append(find_key_in_condition)
                    uil_distance_list, snm_distance_list = self.diction_list(candid_result_in_condition, curr_ct, re_cover_text)
                    # mutiple and find in SNOMED CT
                    if len(self.result_dict) >= 10 and self.ct_find and word_check and self.ct_available_check:
                        print(123)
                        t_name = self.re_organ(pre_data)
                        dist = self.quick_edit_distance(curr_ct, t_name)
                        self.new_dict_incl_distance.append([left_mapping_text, curr_ct, dist,uil_distance_list,snm_distance_list, candid_result_in_condition, [curr_ct], "SNOMED CT", ""])
                        self.result_mapping.append([left_mapping_text,curr_ct, dist, "SNOMED CT"])
                    elif len(self.result_dict)>= 5 and Counter(self.result_dict).most_common(2)[0][1] != Counter(self.result_dict).most_common(2)[1][1]:
                        na, dist = self.cal_distance(pre_data)
                        print("here1")
                        print(self.ct_find)
                        print(curr_ct)
                        if self.ct_find:
                            tmp = self.re_organ(pre_data)
                            dist = self.quick_edit_distance(tmp, curr_ct)
                            self.new_dict_incl_distance.append([left_mapping_text, curr_ct, dist,uil_distance_list,snm_distance_list, candid_result_in_condition, [curr_ct], "UIL", ""])
                            self.result_mapping.append([left_mapping_text,curr_ct, dist, "UIL"])
                        else:
                            self.new_dict_incl_distance.append([left_mapping_text, na, dist,uil_distance_list,snm_distance_list, candid_result_in_condition, [], "UIL", ""])
                            self.result_mapping.append([left_mapping_text,na, dist, "UIL"])
                        
                        # print("highest uil finding")

                    # finding lots of in uil also finding in snomed ct
                    elif len(Counter(self.result_dict)) >=4 and self.ct_find:
                        # print("dfssdf")
                        # base_in_condition = self.re_organ(pre_data)
                        # dist = self.quick_edit_distance(base_in_condition, curr_ct)
                        na, dist = self.cal_distance(pre_data)
                        self.new_dict_incl_distance.append([left_mapping_text, na, dist,uil_distance_list,snm_distance_list, candid_result_in_condition, [curr_ct], "UIL", ""])
                        self.result_mapping.append([left_mapping_text,na, dist,  "UIL"])
                        # self.result_mapping.append([left_mapping_text, curr_ct, "SNOMED CT"])
                        # print("finding lots of in uil also finding in snomed ct")
                    
                    # lots of matched but not snomed ct
                    elif len(self.result_dict) > 2 and Counter(self.result_dict).most_common(2)[0][1] == Counter(self.result_dict).most_common(2)[1][1] and not self.ct_find:
                       
                        na, dist = self.cal_distance(pre_data)
                        self.new_dict_incl_distance.append([left_mapping_text, "Non-Match", 999,uil_distance_list,snm_distance_list, candid_result_in_condition, [], "UIL", ""])
                        self.result_mapping.append([left_mapping_text, "Non-Match", 999, "UIL"])
                        # print("lots of matched but not snomed ct")

                    # find on uil but not find in snomed ct
                    elif len(self.result_dict) > 0 and self.ct_find == False:
                        # print("here")
                        na, dist = self.cal_distance(pre_data)
                        n, s = autoModel([left_mapping_text, Counter(self.result_dict).most_common(1)[0][0]])
                        # print(s)
                        # print(n)
                        # print(na)
                        # print(dist)
                        print(s)
                        print(word_check)
                        print(self.ct_find)
                        if float(s) > 0.5:
                            self.new_dict_incl_distance.append([left_mapping_text, na, dist,uil_distance_list,snm_distance_list, candid_result_in_condition, [], "UIL", ""])
                            self.result_mapping.append([left_mapping_text, na, dist, "UIL"])
                        else:
                        
                            if len(self.result_dict) == 1 and dist <= 15:
                                self.new_dict_incl_distance.append([left_mapping_text, na, dist,uil_distance_list,snm_distance_list, candid_result_in_condition, [], "UIL", ""])
                                self.result_mapping.append([left_mapping_text, na, dist, "UIL"])
                            
                            else:
                                if word_check and 0 < len(self.result_dict) <= 5:
                                    self.new_dict_incl_distance.append([left_mapping_text, na, dist,uil_distance_list,snm_distance_list, candid_result_in_condition, [], "UIL", ""])
                                    self.result_mapping.append([left_mapping_text, na, dist, "UIL"])
                                    
                                else:
                                    print("ss")
                                    self.new_dict_incl_distance.append([left_mapping_text, "Non-Match", 999,uil_distance_list,snm_distance_list, candid_result_in_condition, [], "UIL", ""])
                                    self.result_mapping.append([left_mapping_text,"Non-Match", 999, "UIL"])


                            
                        # print(Counter(self.result_dict).most_common(2)[0][1])
                        # print("find on uil")

                    # find in snomed ct
                    elif len(self.result_dict) > 0 and self.ct_find:
                        print("asdas")
                        na, dist = self.cal_distance(pre_data)
                        if dist <=3:
                            self.new_dict_incl_distance.append([left_mapping_text, na, dist,uil_distance_list,snm_distance_list,candid_result_in_condition, [curr_ct], "UIL", ""])
                            self.result_mapping.append([left_mapping_text, na,dist, "UIL"])
                        elif self.ct_available_check and len(self.result_dict) <= 4:
                            self.new_dict_incl_distance.append([left_mapping_text, na, dist,uil_distance_list,snm_distance_list,candid_result_in_condition, [curr_ct], "UIL", ""])
                            self.result_mapping.append([left_mapping_text, na,dist, "UIL"])
                        else:
                            base_in_condition = self.re_organ(pre_data)
                            dist = self.quick_edit_distance(base_in_condition, curr_ct)
                            self.new_dict_incl_distance.append([left_mapping_text, curr_ct, dist,uil_distance_list,snm_distance_list, candid_result_in_condition, [curr_ct], "SNOMED CT", ""])
                            self.result_mapping.append([left_mapping_text,curr_ct,dist, "SNOMED CT"])
          
                    elif self.ct_find:
                        print("here")
                        base_in_condition = self.re_organ(pre_data)
                        dist = self.quick_edit_distance(base_in_condition, curr_ct)
                        self.new_dict_incl_distance.append([left_mapping_text, curr_ct, dist,uil_distance_list,snm_distance_list, candid_result_in_condition, [curr_ct], "SNOMED CT", ""])
                        self.result_mapping.append([left_mapping_text, curr_ct, dist,"SNOMED CT"])
                        # print("find in snomed ct")
                    else:
                        print("Mapping")
                        base_in_condition = self.re_organ(pre_data)
                        # dist = self.quick_edit_distance(base_in_condition, curr_ct)
                        self.new_dict_incl_distance.append([left_mapping_text, "Non-Match", 9999,uil_distance_list,snm_distance_list, candid_result_in_condition, [], "UIL", ""])
                        self.result_mapping.append([left_mapping_text, "Non-Match", dist, "UIL"])
                
                # find in snomed ct but not relationship with uil
                elif self.ct_find:
                    # print(12343423)
                    if self.ct_available_check and word_check:
                        print("ct")
                        re_cover_text = self.re_organ(pre_data)
                        uil_distance_list, snm_distance_list = self.diction_list(candid_result_in_condition, curr_ct, re_cover_text)
                        # print(curr_ct)
                        # base_in_condition = self.re_organ(pre_data)
                        dist = self.quick_edit_distance(re_cover_text, curr_ct)
                        self.new_dict_incl_distance.append([left_mapping_text, curr_ct, dist,uil_distance_list, snm_distance_list,candid_result_in_condition, [curr_ct], "SNOMED CT", ""])
                        self.result_mapping.append([left_mapping_text, curr_ct, dist,  "SNOMED CT"])
                    elif word_check:
                        print(1234)
                        re_cover_text = self.re_organ(pre_data)
                        uil_distance_list, snm_distance_list = self.diction_list(candid_result_in_condition, curr_ct, re_cover_text)
                        # print(curr_ct)
                        # base_in_condition = self.re_organ(pre_data)
                        dist = self.quick_edit_distance(re_cover_text, curr_ct)
                        self.new_dict_incl_distance.append([left_mapping_text, curr_ct, dist,uil_distance_list, snm_distance_list,candid_result_in_condition, [curr_ct], "SNOMED CT", ""])
                        self.result_mapping.append([left_mapping_text, curr_ct, dist,  "SNOMED CT"])
                    else:
                        print(4512)
                        # re_cover_text = self.re_organ(pre_data)
                        # uil_distance_list, snm_distance_list = self.diction_list(candid_result_in_condition, curr_ct, re_cover_text)
                        # print(curr_ct)
                        # base_in_condition = self.re_organ(pre_data)
                        # dist = self.quick_edit_distance(re_cover_text, curr_ct)
                        re_cover_text = self.re_organ(pre_data)
                        uil_distance_list, snm_distance_list = self.diction_list(candid_result_in_condition, curr_ct, re_cover_text)
                        self.new_dict_incl_distance.append([left_mapping_text, "Non-Match", 999, uil_distance_list, snm_distance_list,candid_result_in_condition, [curr_ct], "UIL", ""])
                        self.result_mapping.append([left_mapping_text, "Non-Match", 999,  "UIL"])
                    # print("find in snomed ct but relationship with uil")
                else:
                    print("last")
                    na, dist = self.cal_distance(pre_data)
                    result = "Non-Match"
                    uil_distance_list, snm_distance_list = self.diction_list(candid_result_in_condition, curr_ct, re_cover_text)
                    self.new_dict_incl_distance.append([left_mapping_text, "Non-Match", 999,uil_distance_list, snm_distance_list, candid_result_in_condition, [], "UIL", ""])
                    self.result_mapping.append([left_mapping_text, result, dist, "UIL"])
                # print(123)
        
        self.writing.data_list_to_csv(self.result_mapping, self.write_file_name)
        self.writing.writing_to_json(self.new_dict_incl_distance, self.write_file_name)
        # return 0
        # return self.writing.writing(self.result_mapping, self.write_file_name)
        
        # return self.result_mapping
    
    # getting feedback from snomed ct
    def ct_search(self,string_name):
        tmp_string = ""
        for ct_i in string_name:
            tmp_string += ct_i.lower()
        for i in range(len(self.uil_list)):
            if tmp_string == self.uil_list[i][0]:
                result=self.uil_list_origan[i][0]
                if result in self.result_dict.keys():
                    self.result_dict[result] += 1
                    self.statement_check = True
                else:
                    self.result_dict[result] = 1
                    self.statement_check = True
        
    # normal search
    def search(self, status):
        if status == 1:
            for i in range(len(self.uil_list)):
                if self.target in self.uil_list[i][0]:
                    result=self.uil_list_origan[i][0]
                    if self.result_dict:
                        if result in self.result_dict.keys():
                            self.result_dict[result] += 1
                            self.statement_check = True

                if self.target in self.uil_list[i][1]:
                    result=self.uil_list_origan[i][0]
                    if self.result_dict:
                        if result in self.result_dict.keys():
                            self.statement_check = True
                            self.result_dict[result] += 1

                if self.target in self.uil_list[i][2]:
                    result=self.uil_list_origan[i][0]
                    if self.result_dict:
                        if result in self.result_dict.keys():
                            self.result_dict[result] += 1
                            self.statement_check = True

                if self.target in self.uil_list[i][4]:
                    result=self.uil_list_origan[i][0]
                    if self.result_dict:
                        if result in self.result_dict.keys():
                            self.result_dict[result] += 1
                            self.statement_check = True
        else:
            for i in range(len(self.uil_list)):

                if self.target in self.uil_list[i][0]:
                    result=self.uil_list_origan[i][0]
                    self.ct_available_check = True
                    if self.result_dict:
                        if result in self.result_dict.keys():
                            self.result_dict[result] += 1
                            self.statement_check = True

                if self.target in self.uil_list[i][1]:
                    result=self.uil_list_origan[i][0]
                    self.ct_available_check = True
                    if self.result_dict:
                        if result in self.result_dict.keys():
                            self.statement_check = True
                            self.result_dict[result] += 1

                if self.target in self.uil_list[i][2]:
                    result=self.uil_list_origan[i][0]
                    self.ct_available_check = True
                    if self.result_dict:
                        if result in self.result_dict.keys():
                            self.result_dict[result] += 1
                            self.statement_check = True

                if self.target in self.uil_list[i][4]:
                    result=self.uil_list_origan[i][0]
                    self.ct_available_check = True
                    if self.result_dict:
                        if result in self.result_dict.keys():
                            self.result_dict[result] += 1
                            self.statement_check = True



    def find_parent(self, target):
        # print(target)
        tmp = ""
        for i in target:
            tmp += i.lower()
        # print(tmp)
        target = tmp
        for i in range(len(self.uil_list)):

            if target in self.uil_list[i][0]:
               
                result=self.uil_list_origan[i][0]
                if result not in self.result_dict.keys():
                    # print(8)
                    self.statement_check = True
                    self.result_dict[result] = 1

            if target in self.uil_list[i][1]:
                result=self.uil_list_origan[i][0]
                if result not in self.result_dict.keys():
                    # print(9)
                    self.statement_check = True
                    self.result_dict[result] = 1

            if target in self.uil_list[i][2]:
                result=self.uil_list_origan[i][0]
                if result not in self.result_dict.keys():
                    # print(10)
                    self.result_dict[result] = 1
                    self.statement_check = True
                    # print(self.result_dict)

            if target in self.uil_list[i][4]:
                result=self.uil_list_origan[i][0]
                if result not in self.result_dict.keys():
                    # print(11)
                    self.statement_check = True
                    self.result_dict[result] = 1

    
    def find_comb(self, target):
        for i in range(len(self.uil_list)):
            if target in self.uil_list[i][0]:
                
                result=self.uil_list_origan[i][0]
                if self.result_dict:
                    if result in self.result_dict.keys():
                        # print(12)
                        self.statement_check = True
                        self.result_dict[result] += 1
                    else:
                        self.statement_check = True
                        self.result_dict[result] = 1
            if target in self.uil_list[i][1]:
                
                result=self.uil_list_origan[i][0]
                if self.result_dict:
                    if result in self.result_dict.keys():
                        # print(13)
                        self.statement_check = True
                        self.result_dict[result] += 1
                    else:
                        self.statement_check = True
                        self.result_dict[result] = 1

            if target in self.uil_list[i][2]:
                result=self.uil_list_origan[i][0]
                if self.result_dict:
                    if result in self.result_dict.keys():
                        # print(14)
                        self.statement_check = True
                        self.result_dict[result] += 1
                    else:
                        self.statement_check = True
                        self.result_dict[result] = 1

            if target in self.uil_list[i][4]:
                result=self.uil_list_origan[i][0]
                if self.result_dict:
                    if result in self.result_dict.keys():
                        # print(15)
                        self.statement_check = True
                        self.result_dict[result] += 1
                    else:
                        self.statement_check = True
                        self.result_dict[result] = 1
        
    def nltk_mapping(self):
        pass
        # print(nltk.pos_tag(nltk.word_tokenize(self.target)))

    def syn_match(self):
        pass
        # print(synonyms.nearby(self.target))

    def history_dictionary(self):
        pass

    def spacy_pos(self, strings):
        doc = self.nlp(strings)
        for i in doc:
            self.parent = i.head.text
            # print(self.parent)
            break

    def re_organ(self, pre_data):
        candi_base = ""
        for tmp_base_distance in pre_data:
            candi_base += tmp_base_distance[0]
            candi_base += " "
        candi_base = candi_base[:-1]
        return candi_base

    def cal_distance(self, pre_data):
        candid = []
        candi_base = ""
        for tmp_base_distance in pre_data:
            candi_base += tmp_base_distance[0]
            candi_base += " "
        candi_base = candi_base[:-1]
        for key_can in self.result_dict.keys():
            candid.append(key_can)
        # string1 = candi_base
        # string2 = 
        distance_result, distance_number = self.edit_distance(candid, candi_base)
        return distance_result, distance_number

    def edit_distance(self, a, b):
        # string1 = copy.deepcopy(a)
        # string2 = copy.deepcopy(b)
        # t11 = ""
        # t22 = ""
        # for i in string1:
        #     t11 += i.lower()

        # for i in string2:
        #     t22 += i.lower()

        min_dist = 999
        min_name = ""
        for i in a:
            string1 = copy.deepcopy(i)
            string2 = copy.deepcopy(b)
            t11 = ""
            t22 = ""
            for iii in string1:
                t11 += iii.lower()

            for iii in string2:
                t22 += iii.lower()
            r = editdistance.eval(t11, t22)
            if r < min_dist:
                # print()
                min_dist = r
                min_name = i

        return min_name, min_dist
    
    def quick_edit_distance(self, a, b):
        string1 = copy.deepcopy(a)
        string2 = copy.deepcopy(b)
        t11 = ""
        t22 = ""
        for jj in string1:
            t11 += jj.lower()

        for jj in string2:
            t22 += jj.lower()
        return editdistance.eval(t11, t22)
    
    def diction_list(self, uil_list, snm, target):
        dis_li = []
        snm_list = []
        if len(uil_list) != 0:
            for i in uil_list:
                r = self.quick_edit_distance(i, target)
                dis_li.append(r)
        if snm != "Not Find":
            snm_list.append(self.quick_edit_distance(snm, target))
        return dis_li, snm_list
    
    def medical_word_check(self, word):
        result = predict_medical_text(self.classifier, self.text_vectorizer, word)
        return result
        # print('Is the Nice weather a medical-related sentence? :', result)