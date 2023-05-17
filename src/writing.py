import pandas
import csv
import json

class writing:
    def __init__(self):
        pass

    def writing(self, result_mapping, file):
        dataframe = pandas.DataFrame(result_mapping, columns=['raw', 'result', 'Flag'])
        dataframe.to_csv(file, index= False)
        processed_csv = dataframe.to_csv(index=False)
        return processed_csv
        # return processed_csv

    def transform_to_json(self,input_data):
        columns = ["raw_data", "out_put_data", "distance", "uil_possible_list", "snomed_ct_possible_list", "result_from"]
        json_data = [dict(zip(columns, row)) for row in input_data]
        return json_data
        
    def data_list_to_csv(self,input_data, name):
        columns = ["raw_data", "out_put_data", "distance", "result_from"]
        with open(name+".csv", "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)
            for row in input_data:
                writer.writerow(row)

    def writing_to_json(self,input_data,nn):
        columns = ["raw_data", "out_put_data", "distance","uil_dist_list","sn_dist_list", "uil_possible_list", "snomed_ct_possible_list", "result_from", "history"]
        json_data = [dict(zip(columns, row)) for row in input_data]
        with open(nn+".json", "w", newline="", encoding="utf-8") as jsonfile:
            json.dump(json_data,jsonfile)
        return json_data