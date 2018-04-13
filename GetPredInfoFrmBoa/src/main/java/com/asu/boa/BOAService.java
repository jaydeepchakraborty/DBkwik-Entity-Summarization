package com.asu.boa;


import java.io.File;
import java.io.IOException;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;

import javax.ws.rs.POST;
import javax.ws.rs.Path;

import org.apache.lucene.document.Document;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.Term;
import org.apache.lucene.search.BooleanClause;
import org.apache.lucene.search.BooleanQuery;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.Sort;
import org.apache.lucene.search.SortField;
import org.apache.lucene.search.TermQuery;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;


@Path("/boaservice")
public class BOAService {

	@POST
    @Path("/getpredinfo")
    public String getPredInfo(String inputJsonObj) throws IOException {
		
		System.out.println(inputJsonObj);
		
		ClassLoader classLoader = getClass().getClassLoader();
        Directory directory = FSDirectory.open(new File(classLoader.getResource("boa_en_10").getFile()));
        IndexReader indexReader = DirectoryReader.open(directory);
        IndexSearcher indexSearcher = new IndexSearcher(indexReader);

        BooleanQuery query = new BooleanQuery();
        query.add(new TermQuery(new Term("nlr-var", inputJsonObj)), BooleanClause.Occur.MUST);

        int numResults = 50;
        Sort sort = new Sort(new SortField(BoaEnum.SUPPORT_NUMBER_OF_PAIRS_LEARNED_FROM.getLabel(), SortField.Type.DOUBLE, true));
        ScoreDoc[] hits = indexSearcher.search(query, numResults, sort).scoreDocs;

        final Set<String> gPattern = new HashSet<>();
        final Set<String> noVarPattern = new HashSet<>();
        final Map<String, BoaPattern> patterns = new LinkedHashMap<String, BoaPattern>();


        for (int i = 0; i < hits.length; i++) {
            final Document doc = indexSearcher.doc(hits[i].doc);
            float score = doc.getField(BoaEnum.SUPPORT_NUMBER_OF_PAIRS_LEARNED_FROM.getLabel())
                    .numericValue().floatValue();

            gPattern.add(doc.getField(BoaEnum.NLR_GEN.getLabel()).stringValue().trim());
            noVarPattern.add(doc.getField(BoaEnum.NLR_NO_VAR.getLabel()).stringValue().trim());

            final BoaPattern pattern = new BoaPattern();
            pattern.naturalLanguageRepresentation =
                    doc.getField(BoaEnum.NLR_VAR.getLabel()).stringValue().trim();
            pattern.generalized = doc.getField(BoaEnum.NLR_GEN.getLabel()).stringValue().trim();
            pattern.naturalLanguageRepresentationWithoutVariables =
                    doc.getField(BoaEnum.NLR_NO_VAR.getLabel()).stringValue().trim();
            pattern.posTags = doc.getField(BoaEnum.POS.getLabel()).stringValue().trim();
            pattern.boaScore =
                    new Double(doc.getField(BoaEnum.SUPPORT_NUMBER_OF_PAIRS_LEARNED_FROM.getLabel())
                            .numericValue().floatValue()//
                    );
            pattern.language = "en";

            final int maxpattern = 10;
            if (!pattern.getNormalized().trim().isEmpty()
                    && !patterns.containsKey(pattern.getNormalized().trim()) && (patterns.size() < maxpattern)) {            	
                patterns.put(pattern.getNormalized().trim(), pattern);
            }

        }

//        System.out.println("patterns size: " + patterns.size());

//        int ind = 0;
//        for(String patternKey : patterns.keySet()) {
//        	System.out.println("Pattern No:- "+ ++ind);
//            System.out.println("1_generalized:- "+patterns.get(patternKey).generalized);
//            System.out.println("2_naturalLanguageRepresentation:- "+patterns.get(patternKey).naturalLanguageRepresentation);
//            System.out.println("3_naturalLanguageRepresentationNormalized:- "+patterns.get(patternKey).naturalLanguageRepresentationNormalized);
//            System.out.println("4_naturalLanguageRepresentationWithoutVariables:- "+patterns.get(patternKey).naturalLanguageRepresentationWithoutVariables);
//            System.out.println("5_getNormalized:- "+patterns.get(patternKey).getNormalized());
//            System.out.println("6_normalize:- "+patterns.get(patternKey).normalize());
//            System.out.println("7_posTags:- "+patterns.get(patternKey).posTags);
//            System.out.println("8_boaScore:- "+patterns.get(patternKey).boaScore);
//            System.out.println("9_naturalLanguageScore:- "+patterns.get(patternKey).naturalLanguageScore);
//            System.out.println("--------------------------------------------");
//        }

        
//        JSONObject outputJsonObj = new JSONObject();
//        outputJsonObj.put("output", "hi");

        String retJsonObj = "";
        
        if(patterns.size() > 0){
        	Entry<String, BoaPattern> entry = patterns.entrySet().iterator().next();
        	 String patternKey= entry.getKey();
        	 retJsonObj=patterns.get(patternKey).getNormalized();
        }else{
        	retJsonObj = inputJsonObj;
        }
        
        return retJsonObj;
        
    }
}
