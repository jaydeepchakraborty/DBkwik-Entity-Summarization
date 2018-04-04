from SPARQLWrapper import SPARQLWrapper, JSON
import nltk, inflect, re, os

def replace_underscore_with_space(string):
    return string.replace('_', ' ')

def get_possessive_form(string):
    if string[-1] == 's':
        return string + "'"
    else:
        return string + "'s"

def combine_conjunctive_sentences(sents):
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
    print(query)
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    output = {}
    for result in results["results"]["bindings"]:
        return result['name']['value']

def get_resource_name(URI):
    wiki = URI.split('/')[3]
    ontology_namespace = "http://dbkwik.webdatacommons.org/" + wiki + "/ontology"
    property_namespace = "http://dbkwik.webdatacommons.org/" + wiki + "/property"
    
    sparql = SPARQLWrapper("http://dbkwik.webdatacommons.org/sparql")
    query = ("""SELECT ?name ?dbr WHERE {        
        # Get English label of URI
        OPTIONAL { <""" + URI + """> <""" + property_namespace + """/name> ?name . FILTER(lang(?name)='en') . }
        OPTIONAL { <""" + URI + """> <http://www.w3.org/2004/02/skos/core#prefLabel> ?name . FILTER(lang(?name)='en') . }       
        OPTIONAL { <""" + URI + """> <http://www.w3.org/2000/01/rdf-schema#label> ?name . FILTER(lang(?name)='en') . }        
        OPTIONAL { <""" + URI + """> <http://www.w3.org/2002/07/owl#sameAs> ?dbr . }
    }
    """)
    print(query)
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    output = {}
    for result in results["results"]["bindings"]:
        if 'name' in result:
            return result['name']['value']
        else: # Fallback to getting label from DBpedia using Same As
            return get_resource_name_from_dbpedia(result['dbr']['value'])                   
    return None

def get_ontology_label(ontology):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    query = ("""SELECT ?label WHERE {        
        <http://dbpedia.org/ontology/""" + ontology + """> rdfs:label ?label .
        FILTER(lang(?label)='en')
    }
    """)
    print(query)
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    output = {}
    for result in results["results"]["bindings"]:
        return result['label']['value']
        
    return replace_underscore_with_space(ontology.lower())

def get_basic_info(URI):
    wiki = URI.split('/')[3]
    ontology_namespace = "http://dbkwik.webdatacommons.org/" + wiki + "/ontology"
    property_namespace = "http://dbkwik.webdatacommons.org/" + wiki + "/property"
    
    sparql = SPARQLWrapper("http://dbkwik.webdatacommons.org/sparql")
    query = ("""SELECT (group_concat(?type;separator='|') as ?types) ?name ?gender ?dbr WHERE {        
        # Get Types of URI
        <""" + URI + """> rdf:type ?type .
        FILTER(contains(str(?type), '""" + ontology_namespace + """')) .
        
        # Get English label of URI
        OPTIONAL { <""" + URI + """> <""" + property_namespace + """/name> ?name . FILTER(lang(?name)='en') . }
        OPTIONAL { <""" + URI + """> <http://www.w3.org/2004/02/skos/core#prefLabel> ?name . FILTER(lang(?name)='en') . }
        OPTIONAL { <""" + URI + """> <http://www.w3.org/2000/01/rdf-schema#label> ?name . FILTER(lang(?name)='en') . }        
                
        # Try to get gender
        OPTIONAL { <""" + URI + """> <""" + property_namespace + """/gender> ?gender . }
        
        # Try to get corresponding DBpedia Resource
        OPTIONAL { <""" + URI + """> owl:sameAs ?dbr . }
    }
    """)
    print(query)
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    output = {}
    for result in results["results"]["bindings"]:
        output = {
            'types': result['types']['value'],            
            'dbr': result['dbr']['value']
        }
        
        if 'name'in result:
            output['name'] = result['name']['value']
        if 'gender' in result:
            output['gender'] = result['gender']['value']
        break
        
    return output

def get_top_k_triples(URI, k):
    wiki = URI.split('/')[3]
    ontology_namespace = "http://dbkwik.webdatacommons.org/" + wiki + "/ontology"
    property_namespace = "http://dbkwik.webdatacommons.org/" + wiki + "/property"
    
    sparql = SPARQLWrapper(os.environ['EC2_URI'])
#     query = ("""SELECT ?predicate ?resource ?r_resource ?rank
#         WHERE {
#           {
#             select ?predicate ?resource ?rank {
#             <""" + URI + """> ?predicate ?resource .
#             ?resource <http://purl.org/voc/vrank#pagerank> ?rank .
#             }
#           }
#           UNION
#           {
#             select ?predicate ?r_resource ?rank {
#             ?r_resource ?predicate <""" + URI + """> .
#             ?r_resource <http://purl.org/voc/vrank#pagerank> ?rank .
#             }
#           }

#           FILTER (?predicate NOT IN (<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>, 
#                 <http://purl.org/dc/terms/subject>, 
#                 <http://xmlns.com/foaf/0.1/depiction>, 
#                 <http://www.w3.org/2002/07/owl#sameAs>, 
#                 <""" + ontology_namespace + """/thumbnail>, 
#                 <""" + property_namespace + """/predecessor>,
#                 <""" + property_namespace + """/successor>, 
#                 <http://xmlns.com/foaf/0.1/isPrimaryTopicOf>, 
#                 <http://xmlns.com/foaf/0.1/primaryTopic>)).
#         } ORDER BY DESC(?rank)
#     """)

#     query = """
#     SELECT ?p ?o ?reverse ?rank {
#         SELECT ?p ?o ?reverse ?rank {
#             {
#                 SELECT ?p ?o ?obj_rank (max(?prop_rank) as ?prop_final_rank) ?reverse {
#                 {<""" + URI + """> ?p ?o . BIND(false as ?reverse)} 
#                 UNION {?o ?p <""" + URI + """> . BIND(true as ?reverse)}
                
#                 FILTER (?p NOT IN (
#                   <http://purl.org/dc/terms/subject>, 
#                   <http://xmlns.com/foaf/0.1/depiction>, 
#                   <http://www.w3.org/2002/07/owl#sameAs>, 
#                   <""" + ontology_namespace + """/thumbnail>, 
#                   <""" + property_namespace + """/predecessor>,
#                   <""" + property_namespace + """/successor>, 
#                   <""" + property_namespace + """/name>, 
#                   <http://xmlns.com/foaf/0.1/isPrimaryTopicOf>, 
#                   <http://xmlns.com/foaf/0.1/primaryTopic>                    
#                 )) .
                
#                 OPTIONAL { <""" + URI + """> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?class . ?p ?class ?prop_rank }
#                 OPTIONAL { ?p <http://purl.org/voc/vrank#proprank> ?prop_rank }
#                 OPTIONAL { ?o <http://purl.org/voc/vrank#pagerank> ?obj_rank }
#                 OPTIONAL {FILTER ISLITERAL(?o) . BIND(0.15 as ?obj_rank) }
#                 } GROUP BY ?p ?o ?obj_rank ?reverse
#             }
# #    BIND(?obj_rank * ?prop_final_rank as ?rank) # PROD RANK
#     BIND(?obj_rank * ?prop_final_rank / (?obj_rank + ?prop_final_rank) as ?rank) # HARMONIC RANK
#   }
# } ORDER BY DESC(?rank)    
#     """

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
    
    print(query)
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    output = {}
    predicates = []
    for result in results["results"]["bindings"]:
        predicate = result['p']['value']

        if predicate not in predicates:
            predicates.append(predicate)
            output[predicate] = {
                'resources': [],
                'label': result['p_label']['value']
            }
        
        obj = {
            'resource': result['o']['value'],
            'rank': result['rank']['value'],
            'reverse': result['reverse']['value']
        }
        
        output[predicate]['resources'].append(obj)        
            
        if len(predicates) == k:
            break
            
    return output