package com.nlp

import java.util.Calendar

import org.apache.spark.SparkConf
import org.apache.spark.sql.SparkSession

object SparkPageRank_final {

  
  val base_path = "/Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/"
//  val db_file_path = base_path + "test.nt"
      val db_file_path = base_path + "dbkwik.nt"
      

  def main(args: Array[String]) {
    try {
      var start_time = Calendar.getInstance().getTime()

      //-----------STEP_1 START------------//
            var loadFileNm = readAndLoadData()
//            println(loadFileNm) ///file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_11520047585103
      //-----------STEP_1 END------------//

      //-----------STEP_2 START------------//
//            var loadFileNm = "file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_11520047585103"
            var indxNodeFileNm = saveNodeIndx(loadFileNm)
//            println(indxNodeFileNm)
//(file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_21520048186469,
//    file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_31520048189429)

      //-----------STEP_2 END------------//

      //-----------STEP_3 START------------//
//            var loadFileNm = "file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_11520047585103"
            var verticesToIndexFlNM = indxNodeFileNm._2
//            var verticesToIndexFlNM = "file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_31520048189429"
            var edgeFlNM = populateEdges(loadFileNm, verticesToIndexFlNM)
//            println(edgeFlNM) //file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_41520048341664
      //-----------STEP_3 END------------//

      //-----------STEP_4 START------------//
//      var edgeFlNM = "file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_41520048341664"
      var graphFlNM = populateGraphDtl(edgeFlNM)
//      println(graphFlNM) //file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_51520066528190
      //-----------STEP_4 END------------//
      
      //-----------STEP_5 START------------//
//      var graphFlNM = "file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_51520066528190"
      var rankFlNM = populateRank(graphFlNM)
//      println(rankFlNM) //file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_61520066921086
      //-----------STEP_5 END------------//

      //-----------STEP_6 START------------//
//            var rankFlNM = "file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_61520066921086"
            var IndexToVerticesFlNM = indxNodeFileNm._1
//            var IndexToVerticesFlNM = "file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_21520048186469"
            var saveRankFlNm = saveRank(rankFlNM, IndexToVerticesFlNM)
//            println(saveRankFlNm)//file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_61517958811115
      //-----------STEP_6 END------------//

      var end_time = Calendar.getInstance().getTime()
      var total_time = end_time.getTime() - start_time.getTime()
      println("Total TIME:- " + start_time + " -- " + end_time + " --> " + total_time)
    } catch {
      case e: Exception => e.fillInStackTrace()
    }
  }

  def getSparkSession(): SparkSession = {

    val conf = new SparkConf().setAppName("page_rank").setMaster("local[*]")
      .set("spark.driver.memory", "6G")
      .set("spark.executor.cores", "2")
      .set("spark.executor.memory", "4G")
      .set("spark.eventLog.enabled", "true")
      .set("spark.eventLog.dir", "/Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576")
    val spark = SparkSession.builder.config(conf).getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark
  }

  def readAndLoadData(): String = {

    try {
      val sp = getSparkSession()
      val inputDbFile = sp.sparkContext.textFile(db_file_path)
      val lines_2 = inputDbFile.map(dbkwikDs)
      val lines = lines_2.filter { x => x != "" }

      val outputPath_1 = "file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_1"
      var fileNm = outputPath_1 + Calendar.getInstance().getTimeInMillis()
      lines.coalesce(1).saveAsTextFile(fileNm);
      sp.close()
      return fileNm
    } catch {
      case e: Exception => e.fillInStackTrace()
    }

    return ""
  }

  def dbkwikDs(line: String): String = {

    var NQ_PATTERN = "^(?:<([^>]+)>\\s*){4}\\s*.".r;
    var NT_PATTERN = "^(?:<([^>]+)>\\s*){3}\\s*.".r;
    var PREFIX_STR = "http://dbkwik.webdatacommons.org";

    if (NQ_PATTERN.pattern.matcher(line).matches || NT_PATTERN.pattern.matcher(line).matches) {
      val fields = line.split(">\\s*")
      if (fields.length > 2 && fields(0).substring(1).startsWith(PREFIX_STR) && fields(2).substring(1).startsWith(PREFIX_STR)) {
        val _subject = fields(0).substring(1)
        val _object = fields(2).substring(1)
        return _subject+ " " +_object
      } else {
        ""
      }
    } else {
      ""
    }

  }

  def saveNodeIndx(dbFlNM: String): (String, String) = {
    try {
      val sp = getSparkSession()

      val lines = sp.sparkContext.textFile(dbFlNM)
      val obj = lines.map(x => x.split("\\s")(0)).distinct()
      val sub = lines.map(x => x.split("\\s")(1)).distinct()
      val verticesWithIndexRdd = obj.union(sub).distinct().zipWithIndex()

      val indexToVertices = verticesWithIndexRdd.map { case (k, v) => v + " " + k }
      val verticesToIndex = verticesWithIndexRdd.map { case (k, v) => k + " " + v }

      val outputPath_2 = "file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_2"
      var fileNm_2 = outputPath_2 + Calendar.getInstance().getTimeInMillis()
      indexToVertices.coalesce(1).saveAsTextFile(fileNm_2);

      val outputPath_3 = "file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_3"
      var fileNm_3 = outputPath_3 + Calendar.getInstance().getTimeInMillis()
      verticesToIndex.coalesce(1).saveAsTextFile(fileNm_3);
      sp.close()
      return (fileNm_2, fileNm_3)
    } catch {
      case e: Exception => e.fillInStackTrace()
    }

    return ("", "")
  }

  def populateEdges(dbFlNM: String, NodeIndxFlNm: String): String = {
    try {
      val sp = getSparkSession()

      val lines = sp.sparkContext.textFile(dbFlNM)
      val verticesToIndex = sp.sparkContext.textFile(NodeIndxFlNm).map { x => x.split("\\s")(0) -> x.split("\\s")(1) }
      val verticesToIndexMap = verticesToIndex.collectAsMap()

      val edges = lines.map(l => verticesToIndexMap(l.split("\\s")(0)).toLong + " " + verticesToIndexMap(l.split("\\s")(1)).toLong)

      val outputPath_4 = "file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_4"
      var fileNm_4 = outputPath_4 + Calendar.getInstance().getTimeInMillis()
      edges.coalesce(1).saveAsTextFile(fileNm_4)

      sp.close()
      return fileNm_4
    } catch {
      case e: Exception => e.fillInStackTrace()
    }

    return ""
  }

  def outLinkLenMtdh(linesMapOutLink:scala.collection.Map[String, Iterable[String]], v:String):Long = {
    if(None == linesMapOutLink.get(v)){
      return 0
    }else{
      return linesMapOutLink.get(v).get.size
    }
  }
  
  def inLinkLenMtdh(linesMapInLink:scala.collection.Map[String, Iterable[String]], v:String): String ={
    if(None == linesMapInLink.get(v)){
      return ""
    }else{
      var tmp = linesMapInLink.get(v).get.mkString(",")
      return tmp
    }
  }
  
  def populateGraphDtl(edgeFlNM: String): String = {
    try {
      val sp = getSparkSession()

      var lines = sp.sparkContext.textFile(edgeFlNM)
      var linesMapInLink = lines.map { x => (x.split("\\s")(1),x.split("\\s")(0)) }.groupByKey().collectAsMap()
      var linesMapOutLink = lines.map { x => (x.split("\\s")(0),x.split("\\s")(1)) }.groupByKey().collectAsMap()
      val obj = lines.map(x => x.split("\\s")(0)).distinct()
      val sub = lines.map(x => x.split("\\s")(1)).distinct()
      val uniqueEntities = obj.union(sub).distinct()
            
      var ranksRdd = uniqueEntities.map(v => v +" "+ inLinkLenMtdh(linesMapInLink,v) +" "+ outLinkLenMtdh(linesMapOutLink,v) +" "+ 0.15)

      val outputPath_5 = "file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_5"
      var fileNm_5 = outputPath_5 + Calendar.getInstance().getTimeInMillis()
      ranksRdd.coalesce(1).saveAsTextFile(fileNm_5)

      sp.close()
      return fileNm_5
    } catch {
      case e: Exception => e.fillInStackTrace()
    }

    return ""
  }
  
  
  def populateRank(graphFlNM: String): String = {
    try {

      val sp = getSparkSession()
      var lines = sp.sparkContext.textFile(graphFlNM)
      var ranks = lines.map { x => (x.split("\\s")(0), (x.split("\\s")(1).split(","),x.split("\\s")(2).toInt,x.split("\\s")(3).toDouble)) }.collectAsMap()
 
      
      val numberOfIterations = 5
      for (i <- 1 to numberOfIterations) {
        var ranks1 = ranks.map(r => (r._1,(r._2._1,r._2._2,calcRank(r._2, ranks))))
        ranks = ranks1
      }
      
      val final_rank = ranks.map(r => r._1 + " "+r._2._3)
      val outputPath_6 = "file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_6"
      var fileNm_6 = outputPath_6 + Calendar.getInstance().getTimeInMillis()
      sp.sparkContext.parallelize(final_rank.toSeq).coalesce(1).saveAsTextFile(fileNm_6)
      sp.close()
      return fileNm_6
    } catch {
      case e: Exception => e.fillInStackTrace()
    }

    return ""
  }

 def calcRank( r: (Array[String],Int, Double), ranks: scala.collection.Map[String, (Array[String],Int, Double)]): Double = {
     
    try {
       val newPgRank = r._1.map { x => (ranks.get(x).get._3 / ranks.get(x).get._2.toDouble) }.sum * 0.85 + 0.15
        return newPgRank
    } catch {
      case e: Exception => e.fillInStackTrace()
    }
    
    return r._3
  }

  def saveRank(rankFlNM: String, IndxNodeFlNm: String): String = {
    try {
      val sp = getSparkSession()

      val lines = sp.sparkContext.textFile(rankFlNM)
      val IndexToVertices = sp.sparkContext.textFile(IndxNodeFlNm).map { x => x.split("\\s")(0) -> x.split("\\s")(1) }
      val IndexToVerticesMap = IndexToVertices.collectAsMap()
//      val rankVal = lines.map(l => IndexToVerticesMap(l.split("\\s")(0)) + " "+ l.split("\\s")(1).toDouble)
      val rankVal = lines.map(l => "<" + IndexToVerticesMap(l.split("\\s")(0)) + ">" + " <http://purl.org/voc/vrank#pagerank> \"" + l.split("\\s")(1).toDouble + "\"^^<http://www.w3.org/2001/XMLSchema#double> .")
      

      val outputPath_7 = "file:///Users/jaydeep/jaydeep_workstation/ASU/Spring2018/NLP_576/file_7"
      var fileNm_7 = outputPath_7 + Calendar.getInstance().getTimeInMillis()
      rankVal.coalesce(1).saveAsTextFile(fileNm_7)

      sp.close()
      return fileNm_7
    } catch {
      case e: Exception => e.fillInStackTrace()
    }

    return ""
  }

}