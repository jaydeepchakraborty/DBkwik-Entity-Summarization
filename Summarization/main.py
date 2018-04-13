import pandas as pd
import numpy as np
from SPARQLWrapper import SPARQLWrapper, JSON
import nltk, inflect, re, string, os
import simplejson as json
import nl_helpers
import shutil
%run nl_helpers

def main():
    #########Module-1 : it will read all the test data and will create directory for each test data.
    ##################  In next modules, We will store all the information i.e. triples associated  
    ##################  with it, it's basic info and top k(10) triples (in json format) in these 
    ##################  directories.   

    #reading all the subjects (from sample test file)
    subj_directory = {}
    with open('test_subj.dat') as f:
        URIs = f.readlines()
        for uri in URIs:
            directory = 'resources/' + uri.rstrip('\n').split('/')[-1]
            if os.path.exists(directory):
                shutil.rmtree(directory)
                os.makedirs(directory)
                subj_directory[uri.rstrip('\n')] = directory
            else:
                os.makedirs(directory)
                subj_directory[uri.rstrip('\n')] = directory

    #Persists all resources with directory info
    outfile = open('resource_directory.json', "w")
    outfile.write(json.dumps(subj_directory, indent=4, sort_keys=True))


    #########Module-2 : it will read all the test data and will fetch all the triples associated with it.
    ##################  and save the information in all_triples.json in each corresponding directories.

    subj_directory = {}
    with open('resource_directory.json') as f:
        subj_directory = json.load(f)

    for uri, directory in subj_directory.items():
        #Fetching all triples for subject(URI)
        all_triples = nl_helpers.get_all_triples(uri);
        #Persists all triples for subject(URI)
        outfile = open(directory+'/all_triples.json', "w")
        outfile.write(json.dumps(all_triples, indent=4, sort_keys=True))
        outfile.close()


    #########Module-3 : it will read all the test data and will fetch first k triples associated with it.
    ##################  it will also fetch the basic information of the subject 
    ##################  and save the information in k_triples.json in each corresponding directories.

    subj_directory = {}
    with open('resource_directory.json') as f:
        subj_directory = json.load(f)

    for uri, directory in subj_directory.items():
        #Read all triples for subject(URI) from JSON file
        all_triples = {}
        with open(directory+'/all_triples.json') as f:
            all_triples = json.load(f)
            #Fetching URI : to fetch basic-info,
            subj_basic_info = nl_helpers.get_basic_info(uri)
            #Fetching top k triples;all_triples: to fetch predicate-info and object-info, k = 10
            pred_info = nl_helpers.get_top_k_triples(subj_basic_info['name'], all_triples , 10);
            
            subj_info = {
            'subj_basic_info': subj_basic_info,
            'pred_info': pred_info
            } 
            
            #Persists k triples for subject(URI)
            outfile = open(directory+'/k_triples.json', "w")
            outfile.write(json.dumps(subj_info, indent=4, sort_keys=True))
            outfile.close()

    #########Module-4 : it will read all the test data and it's all information from the json file(k_triples.json).
    ##################  from that information it will generate summary and save in each corresponding directories. 
    ##################  and save the information in k_triples.json in each corresponding directories.

    subj_directory = {}
    with open('resource_directory.json') as f:
        subj_directory = json.load(f)

    for uri, directory in subj_directory.items():
        summary = ''

        k_triples = {}
        with open(directory+'/k_triples.json') as f:
            k_triples = json.load(f)

        summary = generate_summary(k_triples)
        f=open(directory+'/k_triples.dat', "w+")
        f.write(summary)
        f.close()
        print(summary)
  
if __name__== "__main__":
  main()

print("Guru99")