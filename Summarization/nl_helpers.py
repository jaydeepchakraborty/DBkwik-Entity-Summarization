from SPARQLWrapper import SPARQLWrapper, JSON
import nltk, inflect, re, os
import operator
import requests

EC2_URI = 'http://ec2-52-15-230-2.us-east-2.compute.amazonaws.com:3030/dbkwik/query'
p = inflect.engine()
verb_const = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'] #verb

def test_mtdh():
    return "It is working"


def get_inflect_engine():
    return inflect.engine()

def replace_underscore_with_space(string):
    return string.replace('_', ' ')

def get_possessive_form(string):
    if string[-1] == 's':
        return string + "'"
    else:
        return string + "'s"

def combine_conjunctive_sentences(sents):
    if not sents:
        return ''
    string = sents[0]
    for i in range(1, len(sents)):
        if i == len(sents) - 1:
            string += ' and ' + sents[i]
        else:
            string += ', ' + sents[i]        
    return string

def get_resource_name_from_dbpedia(URI):

    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    query = ("""SELECT ?name ?dbr WHERE {        
        # Get English label of URI
        OPTIONAL { <""" + URI + """> <http://www.w3.org/2000/01/rdf-schema#label> ?name . FILTER(lang(?name)='en') . }        
    }
    """)
    # print(query)
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    output = {}
    for result in results["results"]["bindings"]:
        return result['name']['value'] if 'name' in result else None

def get_resource_name(URI):
    # print(URI)
    wiki = URI.split('/')[3] if len(URI.split('/'))>3 else None

    if wiki == None:
        return None

    ontology_namespace = "http://dbkwik.webdatacommons.org/" + wiki + "/ontology"
    property_namespace = "http://dbkwik.webdatacommons.org/" + wiki + "/property"
    
    sparql = SPARQLWrapper(EC2_URI)
    query = ("""SELECT ?name ?dbr WHERE {        
        # Get English label of URI
        OPTIONAL { <""" + URI + """> <""" + property_namespace + """/name> ?name . FILTER(lang(?name)='en') . }
        OPTIONAL { <""" + URI + """> <http://www.w3.org/2004/02/skos/core#prefLabel> ?name . FILTER(lang(?name)='en') . }       
        OPTIONAL { <""" + URI + """> <http://www.w3.org/2000/01/rdf-schema#label> ?name . FILTER(lang(?name)='en') . }        
        OPTIONAL { <""" + URI + """> <http://www.w3.org/2004/02/skos/core#altLabel> ?name . FILTER(lang(?name)='en') . }
        OPTIONAL { <""" + URI + """> <http://www.w3.org/2002/07/owl#sameAs> ?dbr . }
    }
    """)
    # print(query)
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    name = None
    
    for result in results["results"]["bindings"]:
        if 'name' in result:
            name = result['name']['value']
        elif 'dbr' in result: # Fallback to getting label from DBpedia using Same As
            name = get_resource_name_from_dbpedia(result['dbr']['value'])                                   
        break
    
    if name == None:
        name = replace_underscore_with_space(URI.split('/')[-1].replace('Wikipedia:', ''))
    return name

def get_ontology_label(ontology):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    query = ("""SELECT ?label WHERE {        
        <http://dbpedia.org/ontology/""" + ontology + """> rdfs:label ?label .
        FILTER(lang(?label)='en')
    }
    """)
    # print(query)
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    output = {}
    for result in results["results"]["bindings"]:
        return result['label']['value'] if 'label' in result else None
        
    return replace_underscore_with_space(ontology.lower())


def get_types_sents(types):
    p = get_inflect_engine()
    types_arr = types.split('|')

    types_sents = []
    for i in range(len(types_arr)):
        ontology_type = types_arr[i].split('/')[-1]
        # print(ontology_type)
        if ontology_type.lower() == 'agent': # Ignore Agent
            continue
        
        types_sents.append(p.a(get_ontology_label(ontology_type)))

    return types_sents

def get_basic_info(URI):

    wiki = URI.split('/')[3]
    ontology_namespace = "http://dbkwik.webdatacommons.org/" + wiki + "/ontology"
    property_namespace = "http://dbkwik.webdatacommons.org/" + wiki + "/property"
    
    # sparql = SPARQLWrapper("http://dbkwik.webdatacommons.org/sparql")
    sparql = SPARQLWrapper(EC2_URI)  
    query = ("""SELECT (group_concat(?type;separator='|') as ?types) ?name ?gender ?dbr WHERE {        
        # Get Types of URI
        <""" + URI + """> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?type .
        FILTER(contains(str(?type), '""" + ontology_namespace + """')) .
        
        # Get English label of URI
        OPTIONAL { <""" + URI + """> <""" + property_namespace + """/name> ?name . FILTER(lang(?name)='en') . }
        OPTIONAL { <""" + URI + """> <http://www.w3.org/2004/02/skos/core#prefLabel> ?name . FILTER(lang(?name)='en') . }
        OPTIONAL { <""" + URI + """> <http://www.w3.org/2000/01/rdf-schema#label> ?name . FILTER(lang(?name)='en') . }        
                
        # Try to get gender
        OPTIONAL { <""" + URI + """> <""" + property_namespace + """/gender> ?gender . }
        
        # Try to get corresponding DBpedia Resource
        OPTIONAL { <""" + URI + """> <http://www.w3.org/2002/07/owl#sameAs> ?dbr . }
    } group by ?name ?gender ?dbr
    """)
    # print(query)
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    subj_basic_info = {}

    # print(results)

    for result in results["results"]["bindings"]:
        subj_basic_info = {
            'types': result['types']['value'],            
            'dbr': result['dbr']['value'] if 'dbr' in result else None,
            'types_sents': get_types_sents(result['types']['value'])
        }
        
        if 'name'in result:
            subj_basic_info['name'] = result['name']['value']
        else:
            subj_basic_info['name'] = ''
        if 'gender' in result:
            subj_basic_info['gender'] = result['gender']['value']
        else:
            subj_basic_info['gender'] = ''
        break
        
    return subj_basic_info


#new added
def get_all_triples(URI):
    wiki = URI.split('/')[3]
    ontology_namespace = "http://dbkwik.webdatacommons.org/" + wiki + "/ontology"
    property_namespace = "http://dbkwik.webdatacommons.org/" + wiki + "/property"
    
    sparql = SPARQLWrapper(EC2_URI)
    query = """
    SELECT ?p ?p_label ?o ?prop_final_rank ?obj_rank ?rank ?reverse {
        {
            SELECT ?p ?p_label ?o ?obj_rank (max(?prop_rank) as ?prop_final_rank) ?reverse {
                {<""" + URI + """> ?p ?o . BIND(false as ?reverse)} UNION {?o ?p <""" + URI + """> . BIND(true as ?reverse)}

                FILTER (?p NOT IN (
                    <http://purl.org/dc/terms/subject>, 
                    <http://xmlns.com/foaf/0.1/depiction>, 
                    <http://www.w3.org/2002/07/owl#sameAs>, 
                    <""" + ontology_namespace + """/thumbnail>, 
                    <""" + property_namespace + """/predecessor>,
                    <""" + property_namespace + """/successor>, 
                    <""" + property_namespace + """/name>, 
                    <""" + property_namespace + """/gender>, 
                    <http://xmlns.com/foaf/0.1/isPrimaryTopicOf>, 
                    <http://xmlns.com/foaf/0.1/primaryTopic>                    
                )) .

                ?p <http://www.w3.org/2000/01/rdf-schema#label> ?p_label .
                FILTER(lang(?p_label)='en') .

                OPTIONAL { <""" + URI + """> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?class . ?p ?class ?prop_rank }
                OPTIONAL { ?p <http://purl.org/voc/vrank#proprank> ?prop_rank }
                OPTIONAL { ?o <http://purl.org/voc/vrank#pagerank> ?obj_rank }
                OPTIONAL { FILTER ISLITERAL(?o) . BIND(0.15 as ?obj_rank) }    
            } GROUP BY ?o ?obj_rank ?p ?p_label ?reverse
        }
        #BIND(?obj_rank * ?prop_final_rank as ?rank) # PROD RANK
        BIND(?obj_rank * ?prop_final_rank / (?obj_rank + ?prop_final_rank) as ?rank) # HARMONIC RANK
    } ORDER BY DESC(?rank)    
    """

    # print(query)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return results


def get_pred_pos_tag(subj_nm, pred_nm, objs):
    # print(objs)
    pred_pos = ''
    pred_pos_dict = {}
    for index in range(len(objs)):
        # print(objs[index])
        pos_tag = (nltk.pos_tag([subj_nm  , pred_nm , objs[index]])[1])[1]
        if pred_pos_dict.get(pos_tag) != None:
            pred_pos_dict[pos_tag] = pred_pos_dict.get(pos_tag) + 1
        else:
            pred_pos_dict[pos_tag] = 1

    # for obj_resource in objs["rev_resource_info"]:
    #     pos_tag = (nltk.pos_tag([subj_nm  , pred_nm , obj_resource])[1])[1]
    #     if pred_pos_dict.get(pos_tag) != None:
    #         pred_pos_dict[pos_tag] = pred_pos_dict.get(pos_tag) + 1
    #     else:
    #         pred_pos_dict[pos_tag] = 1

    sorted(pred_pos_dict.items(), key=operator.itemgetter(1))

    # print(pred_pos_dict)
    # print(list(pred_pos_dict.keys()))
    frst_key = list(pred_pos_dict.keys())[0] if list(pred_pos_dict.keys()) else None
    pred_pos = frst_key

    return pred_pos


def get_resource_info(resource_uri_litval, resource_rev_ind):
    resources = []
    r_resources = []

    if resource_uri_litval.startswith('http://'): # URI
            # resource_name = get_resource_name(resource_uri_litval)
            resources = [get_resource_name(resource_uri_litval)]
    else: # Literal
        resource_name = None
        if resource_uri_litval[0] == '*': # Possibly bullet list which was not properly parsed by DBkwik
            _resources = resource_uri_litval.split('*')
            if len(_resources) > 1: # Then probably a bullet list
                _resources = _resources[1:]
                for index2 in range(len(_resources)):
                    _resources[index2] = re.sub(r'[^a-zA-Z0-9 \n\.]', '', _resources[index2]).replace('{', '').replace('}', '').strip()

                resources = _resources
                # if resource_rev_ind == 'true':
                #     r_resources += _resources
                # else:
                #     resources += _resources
        else:
            # resource_name = resource_uri_litval.replace('{', '').replace('}', '') # Handling parsing error where entity might have {}
            resources = [resource_uri_litval.replace('{', '').replace('}', '')] # Handling parsing error where entity might have {}]

        # if resource_name != None: # Continue to next element if resource name was not properly set
        #     resources = [resource_name]
        #     if resource_rev_ind == 'true':
        #         if(len(r_resources) <= 3):
        #             r_resources.append(resource_name)
        #     else:
        #         if(len(resources) <= 3):
        #             resources.append(resource_name)

    # return resources, r_resources
    return resources


def get_top_k_triples(subj_nm, all_triples , k):

    output = {}
    predicates = []
    for triple in all_triples["results"]["bindings"]:
        # print(all_triple)
        # break
        predicate = triple['p']['value']

        if predicate not in predicates:
            predicates.append(predicate)
            output[predicate] = {
                'resources': [],
                'r_resources': [],
                'label': triple['p_label']['value']
                # 'pred_pos_tag': get_pred_pos_tag(subj_nm, triple['p_label']['value'], obj)                
            }


        # resource_info, r_resource_info = get_resource_info(triple['o']['value'], triple['reverse']['value'])
        if triple['reverse']['value'] == 'true':
            output[predicate]['r_resources'] += get_resource_info(triple['o']['value'], triple['reverse']['value'])
        else:
            output[predicate]['resources'] += get_resource_info(triple['o']['value'], triple['reverse']['value'])

        # resource_info, r_resource_info = get_resource_info(triple['o']['value'], triple['reverse']['value'])


        # obj = {
        #     'resource': triple['o']['value'],
        #     'rank': triple['rank']['value'] if 'rank' in triple else None,
        #     'reverse': triple['reverse']['value'],
        #     'resource_info':resource_info,
        #     'rev_resource_info':r_resource_info
        # }

        
        # output[predicate]['resources'].append(obj)
        # output[predicate]['pred_pos_tag'] = get_pred_pos_tag(subj_nm, triple['p_label']['value'], obj)
            
        if len(predicates) == k:
            break

    return output



def get_pred_fillers(predicate_name):
    request = requests.post("http://localhost:8080/GetPredInfoFrmBoa/rest/boaservice/getpredinfo", data=predicate_name)
    return request.text


def generate_predicate_summary(pronoun, possessive_pronoun, predicate_name, pos_tag, resources):
    summary = ''
    # https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html
    if pos_tag in verb_const: #verb
        pred_with_fillers = get_pred_fillers(predicate_name)
        summary += pronoun + ' ' + str(pred_with_fillers) + ' ' + combine_conjunctive_sentences(resources) + '. '
    else:
        if len(resources) == 1: 
            if p.singular_noun(predicate_name) == False or p.singular_noun(predicate_name) == predicate_name: # If singular predicate or plural and singular forms are the same (eg: species)                 
                summary += possessive_pronoun + ' ' + predicate_name + ' is ' + resources[0] + '. '
            else:
                summary += possessive_pronoun + ' ' + predicate_name + ' are ' + resources[0] + '. '
        elif len(resources) > 1:
            if p.singular_noun(predicate_name) == False: # Convert to plural form
                predicate_name = p.plural(predicate_name)
            summary += possessive_pronoun + ' ' + predicate_name + ' are ' + combine_conjunctive_sentences(resources) + '. '        
    return summary

def generate_reverse_predicate_summary(name, predicate_name, pos_tag, resources):
    summary = ''
    if pos_tag in verb_const: #verb
        pred_with_fillers = get_pred_fillers(predicate_name)
        # summary += pronoun + ' ' + str(pred_with_fillers) + ' ' + combine_conjunctive_sentences(resources) + '. '
        summary += combine_conjunctive_sentences(resources) + ' ' + str(pred_with_fillers) + name + '. '
    else:
        resources = [get_possessive_form(resource) for resource in resources]
        if p.singular_noun(predicate_name):
            predicate_name = p.singular_noun(predicate_name)
        summary += combine_conjunctive_sentences(resources) + ' ' + predicate_name + ' is ' + name + '. '

    return summary

def generate_summary(k_triples):
    summary = ''    

    basic_info = k_triples['subj_basic_info']
    name = basic_info['name']

    types_sents = basic_info['types_sents']
    if types_sents != None:
        summary += name + ' is '
        summary += combine_conjunctive_sentences(types_sents) + '. '

    pronoun = 'It'
    possessive_pronoun = 'It\'s'
    if basic_info['gender'].lower() == 'male':
        pronoun = 'He'
        possessive_pronoun = 'His'
        summary += 'His gender is male. '
    elif basic_info['gender'].lower() == 'female':
        pronoun = 'She'
        possessive_pronoun = 'Her'
        summary += 'Her gender is female. '



    for predicate in k_triples['pred_info']:
        predicate_object = k_triples['pred_info'][predicate]

        pred = k_triples['pred_info'][predicate]
        predicate_name = pred['label']

        pos_tag = get_pred_pos_tag(name, predicate_name, predicate_object['resources'] + predicate_object['r_resources'])                

        if len(predicate_object['resources']) > 0:
            summary += generate_predicate_summary(pronoun, possessive_pronoun, predicate_name, pos_tag, predicate_object['resources'][0:3])            

        if len(predicate_object['r_resources']) > 0:
            summary += generate_reverse_predicate_summary(name, predicate_name, pos_tag, predicate_object['r_resources'][:3])            


        # for index in range(len(pred['resources'])):
        #     resource = pred['resources'][index] 

        #     resources = resource['resource_info']
        #     r_resources = resource['rev_resource_info']
        #     # https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html
        #     if pred['pred_pos_tag'] in ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']: #verb
        #         pred_with_fillers = get_pred_fillers(predicate_name)
        #         summary += pronoun + ' ' +str(pred_with_fillers) + ' ' +combine_conjunctive_sentences(resources) + '. '
        #     else:
        #         if len(resources) == 1:
        #             if p.singular_noun(predicate_name) == False or p.singular_noun(predicate_name) == predicate_name: 
        #             # If singular predicate or plural and singular forms are the same (eg: species)
        #                 summary += possessive_pronoun + ' ' + predicate_name + ' is ' + resources[0] + '. '
        #             else:
        #                 summary += possessive_pronoun + ' ' + predicate_name + ' are ' + resources[0] + '. '
        #         elif len(resources) > 1:
        #             if p.singular_noun(predicate_name) == False: # Convert to plural form
        #                 predicate_name = p.plural(predicate_name)
        #             summary += possessive_pronoun + ' ' + predicate_name + ' are ' + combine_conjunctive_sentences(resources) + '. '

        #         if len(r_resources) > 0:
        #             r_resources = [get_possessive_form(resource) for resource in r_resources]
        #             if p.singular_noun(predicate_name):
        #                 predicate_name = p.singular_noun(predicate_name)
        #             summary += combine_conjunctive_sentences(r_resources) + ' ' + predicate_name + ' is ' + name + '. '

    return summary