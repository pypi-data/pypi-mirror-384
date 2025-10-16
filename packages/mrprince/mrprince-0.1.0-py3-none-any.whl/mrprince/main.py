"""
MrPrince - PySpark Code Snippets Library

This module provides PySpark code snippets for various data processing tasks.
"""

def program(num):
    """
    Display PySpark code snippets based on the category number.
    
    Args:
        num (int): Category number (1-10)
            1: RDD Operations
            2: DataFrame Operations
            3: Filtering and Grouping
            4: File Operations
            5: SQL Operations
            6: String Functions
            7: Window Functions
            9: Hyperparameter Tuning
            10: ML Pipelines
    
    Returns:
        None: Prints the code snippet to stdout
    
    Raises:
        ValueError: If num is not between 1-10 (excluding 8)
    """
    if num not in [1, 2, 3, 4, 5, 6, 7, 9, 10]:
        raise ValueError(f"Invalid category number: {num}. Must be 1-7, 9, or 10.")
    
    if(num == 1):
        print("""from google.colab import drive
drive.mount('/content/drive')
!pip install pyspark

from pyspark.sql import SparkSession
spark = SparkSession.builder.master("local[2]").appName("SparkByExamples.com").getOrCreate()

sc = spark.sparkContext
data = [10,20,30,40,50,60,70,80,90,100,110,120,130,140,150]
rdd = sc.parallelize(data)
print(rdd.count())

sc = spark.sparkContext
data = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,100,200,300,400,500]
rdd = sc.parallelize(data)
print(rdd.collect())

print(rdd.first())

from pyspark import SparkContext
spark = SparkContext
data = [0,10,200,30,400,50,600,70,800,90,100,110,120,130]
rdd = sc.parallelize(data)
print(rdd.take(5))

spark = SparkContext.getOrCreate()
data = [1,2,3,4,50]
rdd = spark.parallelize(data)
print(rdd.reduce(lambda x, y : x + y))

sc = SparkContext.getOrCreate()
reduce_rdd = sc.parallelize([10,30,40,60])
print(reduce_rdd.reduce(lambda x, y : x + y))

from pyspark import SparkContext
sc = SparkContext.getOrCreate()
save_rdd = sc.parallelize([1,2,3,4,5,6],numSlices=6)
save_rdd.saveAsTextFile('file89.txt')

spark = SparkSession.builder.master("local[2]").appName("TakeSampleExample").getOrCreate()
rdd = spark.sparkContext.parallelize([1, 1, 3, 2, 4,5,6,8])
sample_with_replacement = rdd.takeSample(withReplacement=True, num=5, seed=42)
print("Sample with replacement:", sample_with_replacement)
sample_without_replacement = rdd.takeSample(withReplacement=False, num=5, seed=42)
print("Sample without replacement:", sample_without_replacement)
spark.stop()

spark = SparkSession.builder.master("local[2]").appName("TakeOrderedExample").getOrCreate()
rdd = spark.sparkContext.parallelize([999,1000,888,444,222,555,111,777,666,333])
smallest_five = rdd.takeOrdered(5)
print("Smallest 5 elements:", smallest_five)
largest_five = rdd.takeOrdered(5, key=lambda x: -x)
print("Largest 5 elements:", largest_five)
spark.stop()

spark = SparkSession.builder.master("local[2]").appName("SaveAsSequenceFileExample").getOrCreate()
rdd = spark.sparkContext.parallelize([("key1", 1), ("key2", 2), ("key3", 3)])
rdd.saveAsSequenceFile("sequence_file-1")
spark.stop()

spark = SparkSession.builder.master("local[2]").appName("SaveAsSequenceFileExample").getOrCreate()
spark.conf.set("dfs.checksum.enabled", "false")
rdd = spark.sparkContext.sequenceFile("sequence_file-1")
rdd.collect()

spark = SparkSession.builder.master("local[2]").appName("SaveAsPickleFileExample").getOrCreate()
rdd = spark.sparkContext.parallelize([("key1", 1), ("key2", 2), ("key3", 3)])
rdd.saveAsPickleFile("pickle-file")
spark.stop()

spark = SparkSession.builder.master("local[2]").appName("ReadPickleFileExample").getOrCreate()
rdd = spark.sparkContext.pickleFile("pickle-file")
print(rdd.collect())
spark.stop()

from pyspark.sql import SparkSession
spark = SparkSession.builder.master("local[2]").appName("CountByKeyExample").getOrCreate()
rdd = spark.sparkContext.parallelize([("apple", 1), ("banana", 1), ("apple", 2), ("banana", 3), ("banana", 4)])
counts = rdd.countByKey()
print(counts)
spark.stop()

spark = SparkSession.builder.master("local[2]").appName("ForeachExample").getOrCreate()
rdd = spark.sparkContext.parallelize([100, 200, 300, 400, 500])
for element in rdd.collect():
    print(f"Element: {element}")
spark.stop()

sc = SparkContext.getOrCreate()
my_rdd = sc.parallelize([10,60,30,40])
print(my_rdd.map(lambda x: x+ 10).collect())""")
        
    elif(num == 2):
        print("""!pip install pyspark

from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("Data Processing Pipeline").getOrCreate()
df = spark.read.csv("/content/GlobalLandTemperaturesByCity.csv", header=True, inferSchema=False)

type(df)

df.select(df['City'],df['Country']).show(n=15)

df.select(df['Latitude'],df['Longitude']).show(n=25)

print(" The datatype of columns is:")
print(df.dtypes)

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
spark = SparkSession.builder.appName("example").getOrCreate()
schema = StructType([
    StructField("id", IntegerType(), True),
    StructField("name", StringType(), True),
    StructField("address", StructType([
        StructField("street", StringType(), True),
        StructField("city", StringType(), True),
        StructField("zip", StringType(), True)
    ]), True)
])

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
spark = SparkSession.builder.appName("example").getOrCreate()
schema = StructType([
    StructField("id", IntegerType(), True),
    StructField("name", StringType(), True),
    StructField("address", StructType([
        StructField("street", StringType(), True),
        StructField("city", StringType(), True),
        StructField("zip", StringType(), True)
    ]), True)
])
data = [
    (1, "Alice", ("123 Main St", "Anytown", "12345")),
    (2, "Bob", ("456 Oak Ave", "Otherville", "67890")),
    (3, "Charlie", ("789 Pine Ln", "Anytown", "12345"))
]
df = spark.createDataFrame(data, schema)
df.show()
print(df.dtypes)

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, StringType
spark = SparkSession.builder.appName("example").getOrCreate()
schema_nullable = StructType([
    StructField("id", IntegerType(), True),
    StructField("name", StringType(), True)
])
schema_non_nullable = StructType([
    StructField("id", IntegerType(), False),
    StructField("name", StringType(), True)
])
data_nullable = [
    (1, "Alice"),
    (2, None),
    (3, "Charlie")
]
data_non_nullable = [
    (1, "Alice"),
    (2, "Bob"),
    (3, "Charlie")
]
df_nullable = spark.createDataFrame(data_nullable, schema_nullable)
df_non_nullable = spark.createDataFrame(data_non_nullable, schema_non_nullable)
print("DataFrame with Nullable Field:")
df_nullable.show()
print("\nDataFrame with Non-Nullable Field:")
df_non_nullable.show()

!pip install pyspark
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("example").getOrCreate()
df = spark.read.csv("/content/GlobalLandTemperaturesByState.csv", sep='@', header=True, inferSchema=True)
df.show()

df.write.csv("processing1.csv")

df.write.format("csv").mode('overwrite').save("/content/res")
df2 = spark.read.csv("/content/GlobalTemperatures.csv", header=True, inferSchema=True)
type(df2)

df2.show(truncate=True)

df2.show(truncate=False)

from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("example").getOrCreate()
print(df.printschema())

from pyspark.sql import SparkSession
from pyspark.sql.functions import max, avg
spark = SparkSession.builder.appName("example").getOrCreate()
df = spark.read.csv("/content/GlobalLandTemperaturesByCountry.csv", header=True, inferSchema=True)
df.show()
print(f"Number of rows: {df.count()}")
df.select(df["Country"], df["AverageTemperature"]).show(n=5)
df.filter(df["Country"] == "Canada").show()
df.groupBy("Country").agg(avg("AverageTemperature").alias("AverageTemperatureByCountry")).show()
df.select(max("AverageTemperature")).show(truncate=False)""")
        
    elif(num == 3):
        print("""!pip install pyspark

from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("sparkdataframes").getOrCreate()
data = [(1,"aravind", "DataAnalyst", 28000,"Rahul"),
        (2,"Banu", "Analyst", 22000,"Vetri"),
        (3,"Cibi", "Manager", 35000,"Swetha"),
        (4,"Rithu", "Manager", 35000,"Ram"),
         (5,"Hari", "Manager", 35000,"kumar"),
        (6,"Devi", "Engineer", 3000,"Nalini")]
columns = ["Empid", "EMP_NAME", "POSITION","SALARY","Manager"]

df = spark.createDataFrame(data,columns)
df.show()

df.printSchema()

df.show(n=2,truncate=25)

df.show(n=3,truncate=2)

df.select("*").show()

df.select(df.columns[1:4]).show(3)

datacollect = df.collect()
print(datacollect)

df.collect()

df.filter(df.Manager=="kumar").show(truncate=False)

df.filter(~(df.Manager=="kumar")).show(truncate=False)

df.filter(df.Manager!="kumar").show()

df.filter("Manager<>'kumar'").show()

df.filter((df.POSITION=="Manager") & (df.Empid=="4")).show()

df.filter((df.POSITION=="Manager") | (df.Empid=="4")).show()

list = ["Nalini","Rahul","Vetri"]
df.filter(df.Manager.isin(list)).show()

list = ["Nalini","Rahul"]
df.filter(df.Manager.isin(list)).show(truncate="3")

list = ["Nalini","Rahul","Vetri"]
df.filter(df.Manager.isin(list)==False).show()

list = ["Nalini","Rahul","Vetri"]
df.filter(df.Manager.isin(list)==True).show()

df.filter(df.EMP_NAME.startswith("B")).show()

df.filter(df.EMP_NAME.endswith("u")).show()

df.filter(df.EMP_NAME.contains("h")).show()

df.show()

df.filter(df.POSITION.like("D%")).show()

df.filter(df.POSITION.like("%t")).show()

df.filter(df.POSITION.like("%a%")).show()

df.filter(df.POSITION.like("%i%")).show()

df.sort("EMP_NAME").show()

df.sort("Empid","EMP_NAME").show()

df.orderBy("SALARY","Empid").show()

df.sort(df.POSITION.asc(),df.Empid.asc()).show()

df.sort(df.POSITION.desc(),df.EMP_NAME.asc()).show()

customerdata = [(1,"ABi",9089078901,"Tamilnadu",18,3245),
              (2,"william",889078901,"Kerala",28,111),
              (3,"xavier",789078901,"Karnataka",38,121),
              (4,"john",9012078901,"Tamilnadu",48,123),
              (5,"chitu",9089078934,"Andhra",58,111),
              (6,"saran",9089078661,"Madya",18,444),
              (7,"prave",96789000001,"Jammu",23,555),
              (8,"parvathy",9089700901,"Goa",24,666),
              (9,"xena",90780078901,"Punjab",33,777),
              (10,"Haier",912349078901,"Srilanka",36,8888),
              (11,"UUII",9089078901,"Rajasthan",17,9000),
              (12,"Zenith",9089078901,"Gujarat",16,1234),
              (13,"ABirami",9089078901,"Uttra Pradesh",10,1112),
              (14,"preetha",9089078901,"Tamilnadu",8,3245),
              ]
schema = ["Id","Name","Phone","state","age","cost"]
df = spark.createDataFrame(data=customerdata,schema=schema)
df.printSchema()
df.show(truncate=False)

df.groupBy("state").sum("cost").show()

df.groupBy("state").count().show()

df.groupBy("state").min("cost").show()

df.groupBy("state").max("cost").show()

df.groupBy("state").avg("cost").show()

df.groupBy("state").mean("cost").show()

df.groupBy("state","age").sum("cost").show()

from pyspark.sql.functions import sum,avg,max,col
df.groupBy("state").agg(sum("cost")).show()

df.groupBy("state").agg(sum("cost").alias("sum_cost"),
                        avg("cost").alias("avg_cost"),
                        max("cost").alias("max_cost")).show()

df.groupBy("state").agg(sum("cost").alias("sum_cost"),
                        avg("cost").alias("avg_cost"),
                        max("cost").alias("max_cost")).where(col("sum_cost")>=1000).show()

df.show()
df.select(max("cost")).show()""")
    
    elif(num == 4):
        print("""!pip install pyspark

from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("Temperature").getOrCreate()
sc = spark.sparkContext
lines = sc.textFile("/content/weather.csv")
lines2 = spark.read.csv("/content/weather.csv")
print(lines2)

header = lines.first()
print(header)
lines = lines.filter(lambda line: line != header)
print(lines.collect())

city_temperature = lines.map(lambda x: x.split(','))
print(city_temperature.collect())

city_temp = city_temperature.map(lambda x: (x[0], x[1]))
print(city_temp.collect())
print(type(city_temp))

city_max_temp = city_temperature.map(lambda x: x[1]).max()
print("City with Max Temperature:", city_max_temp)
city_min_temp = city_temperature.map(lambda x: x[1]).min()
print("City with Min Temperature:", city_min_temp)

from pyspark.sql import SparkSession
from pyspark.sql.functions import max, col
spark = SparkSession.builder.appName("MaxTemperature").getOrCreate()
weather_df = spark.read.csv("/content/city_temperature.csv", header=True, inferSchema=True)
max_temp_value = weather_df.select(max("AvgTemperature").alias("MaxTemperature")).collect()[0]["MaxTemperature"]
max_temp_row = weather_df.filter(col("AvgTemperature") == max_temp_value)
max_temp_row.show()
max_temp_cities = max_temp_row.select("City")
max_temp_cities.show()

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, min, max, split
import pandas as pd
spark = SparkSession.builder.appName("CompareTemperature").getOrCreate()
csv_df = spark.read.csv("/content/min_temperature.csv", header=True, inferSchema=True).select("City", "Temperature")
print("CSV file")
csv_df.show()

text_df = spark.read.text("/content/min_temperature.txt")
header = text_df.first()[0]
data_df = text_df.filter(text_df["value"] != header)
text_df1 = data_df.select(
    split('value', ',').getItem(0).alias("City"),
    split('value', ',').getItem(1).alias("Temperature")
)
print("Text file")
text_df1.show()

csv_min = csv_df.select(min("Temperature")).collect()[0][0]
text_min = text_df1.select(min("Temperature")).collect()[0][0]
if csv_min < text_min:
    print("Minimum temperature is in CSV file:", csv_min)
elif text_min < csv_min:
    print("Minimum temperature is in Text file:", text_min)
else:
    print("Both files have same minimum temperature:", csv_min)
""")
        
    elif(num == 5):
        print("""!pip install pyspark

from pyspark.sql import SparkSession
from os.path import abspath
spark_1 = SparkSession.builder.master("local[1]").appName("SparkByExamples.com").getOrCreate()

data = [("Alice", 28), ("Bob", 22), ("Charlie", 35)]
columns = ["name", "age"]
df_1 = spark_1.createDataFrame(data, columns)

df_1.createOrReplaceTempView("people_1")

df_1.write.saveAsTable("new_table_name_1", format="parquet", mode="overwrite")

spark_1.sql("DESCRIBE new_table_name_1").show()

spark_1.sql("SHOW COLUMNS FROM new_table_name_1").show()

from pyspark.sql import functions as F

df_1.withColumn("new_column", F.lit("some_value")).write.saveAsTable("people_with_new_column_1")

spark_1.sql("DESCRIBE people_with_new_column_1").show()

spark_1.catalog.dropTempView("new_table_name_1")
spark_1.sql("DROP TABLE IF EXISTS new_table_name_1")

new_data = [("David", 30,"Erode"),("Bob", 45,"Coimbatore")]
columns = ["name", "age","new_column"]
new_df = spark_1.createDataFrame(new_data, columns)
new_df.write.insertInto("people_with_new_column_1")
new_df.show()

person_name = "David"
new_age = 56

updated_df = new_df.withColumn("age", F.when(F.col("name") == person_name, new_age).otherwise(F.col("age")))
updated_df.show()
new_df.show()

updated_df = updated_df.filter(F.col("name") != "Bob")
updated_df.show()

from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("MySparkApp").enableHiveSupport().getOrCreate()
from pyspark.sql import functions as F
data = [("Alice", 28), ("Bob", 22), ("Charlie", 35)]
columns = ["name", "age"]
df = spark.createDataFrame(data, columns)
df.show()
print(type(df))

df.createOrReplaceTempView("people")
result = spark.sql("SELECT * FROM people")
result.show()

result = spark.sql("SELECT * FROM people WHERE age > 25")
result.show()

df.write.saveAsTable("new_table_name_2")

df.printSchema()

spark.sql("DESCRIBE new_table_name_2").show()

spark.sql("SHOW COLUMNS FROM new_table_name_2").show()

spark.sql("ALTER TABLE new_table_name_2 ADD COLUMN new_column STRING")

spark.sql("DESCRIBE new_table_name_2").show()

spark.sql("SELECT * FROM new_table_name_2").show()

df = spark.read.table("new_table_name_2")
df.show()

from pyspark.sql.functions import expr
updated_df = df.withColumn("age_plus_5", expr("age + 5"))
updated_df.show()

updated_df = df.withColumn("age", expr("age + 1"))
updated_df.show()

from pyspark.sql.functions import when
updated_df = df.withColumn("is_adult", when(expr("age >= 18"), "Yes").otherwise("No"))
updated_df.show()

from pyspark.sql.functions import col

update_condition = (col("name") == "Bob")
updated_df = df.withColumn("age", when(update_condition, 25).otherwise(col("age")))
updated_df.show()

update_condition = (col("name") == "Bob")
updated_df = df.withColumn("new_column", when(update_condition, "PSG").otherwise(col("new_column")))
updated_df.show()

update_condition = (col("name") == "Alice1")
updated_df = df.withColumn("new_column", when(update_condition, "PSG").otherwise(col("new_column")))
updated_df.show()

from pyspark.sql.functions import lit
job_value = "Engineer"
df_with_job = df.withColumn("job", lit(job_value))
df_with_job.show()

from pyspark.sql.types import StringType
update_condition = (col("name").isin(["Alice", "Charlie"]))

job_update_expr = when(update_condition, "Senior Engr" ).otherwise(col("job")).cast(StringType())
age_update_expr = when(update_condition, col("age") + 5).otherwise(col("age"))

updated_df = df_with_job.withColumn("job", job_update_expr).withColumn("age", age_update_expr)

print("Updated DataFrame:")
updated_df.show()""")
    
    elif(num == 6):
        print("""!pip install pyspark
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("StringFunctionsExample").getOrCreate()

data = [("MacBook Pro", "Laptop", "2023"),
        ("Dell XPS 13", "Ultrabook", "2023"),
        ("Lenovo ThinkPad X1", "Business", "2023"),
        ("HP Spectre x360", "Convertible", "2023"),
        ("Asus ROG Zephyrus", "Gaming", "2023")]
columns = ["model", "type", "year"]

df = spark.createDataFrame(data, columns)
df.createOrReplaceTempView("cars")

concatenated_df = spark.sql("SELECT concat_ws(' - ', model, type, year) AS details FROM cars")
print("1. Concatenated Strings:")
concatenated_df.show(truncate=False)

length_df = spark.sql("SELECT model, length(type) AS type_length FROM cars")
print("2. Length of Types:")
length_df.show()

substring_df = spark.sql("SELECT model, substring(type, 1, 4) AS type_abbr FROM cars")
print("3. Substring of Types:")
substring_df.show()

uppercase_df = spark.sql("SELECT model, type, upper(type) AS uppercase_type FROM cars")
print("4. Uppercase Types:")
uppercase_df.show()

lowercase_df = spark.sql("SELECT model, type, lower(type) AS lowercase_type FROM cars")
print("5. Lowercase Types:")
lowercase_df.show()

from pyspark.sql.functions import base64
from pyspark.sql.functions import col

encoded_df = df.withColumn("model_base64", base64(col("model")))
encoded_df.show()

from pyspark.sql.functions import ascii

ascii_df = df.withColumn("model_ascii", ascii(col("model")))
ascii_df.show()

from pyspark.sql.functions import concat_ws

concatenated_df = df.withColumn("details", concat_ws("-", col("model"), col("type"), col("year")))
concatenated_df.show()

from pyspark.sql.functions import length

length_df = df.withColumn("model_length", length(col("model")))
length_df.show()

from pyspark.sql.functions import instr

position_df = df.withColumn("camry_position", instr(col("model"), "Camry"))
position_df.show()

from pyspark.sql.functions import col, levenshtein

data = [("Apple", "red"),
        ("Banana", "Yellow"),
        ("hello", "world")]
columns = ["string1", "string2"]

df = spark.createDataFrame(data, columns)
distance_df = df.withColumn("levenshtein_distance", levenshtein(col("string1"), col("string2")))
distance_df.show()

from pyspark.sql import SparkSession
from pyspark.sql.functions import ltrim,trim

spark = SparkSession.builder.appName("Trim Example").getOrCreate()

data = [("Apple", "red"),
        ("Banana", "Yellow"),
        ("hello", "world")]
columns = ["string1", "string2"]

df = spark.createDataFrame(data, columns)
trimmed_df = df.withColumn("string1_trimmed", ltrim(df['string1']))
trimmed_df.show()

trimmed_df1 = df.withColumn("string1_trimmed", trim(df['string1']))
trimmed_df1.show()

from pyspark.sql import SparkSession
from pyspark.sql.functions import locate, col

spark = SparkSession.builder.appName("Locate Example").getOrCreate()

data = [("Apple", "red"),
        ("Banana", "Yellow"),
        ("hello", "world")]
columns = ["string1", "string2"]

df = spark.createDataFrame(data, columns)
position_df = df.withColumn("sedan_position", locate("Sedan", col("string2"), 1))
position_df.show()

from pyspark.sql import SparkSession
from pyspark.sql.functions import regexp_replace, col

spark = SparkSession.builder.appName("Regexp Replace Example").getOrCreate()

data = [("Apple", "red"),
        ("Banana", "Yellow"),
        ("hello", "world")]
columns = ["string1", "string2"]

df = spark.createDataFrame(data, columns)
replaced_df = df.withColumn("string2_replaced", regexp_replace(col("string2"), "Sedan", "Compact"))
replaced_df.show()

from pyspark.sql import SparkSession
from pyspark.sql.functions import initcap, col

spark = SparkSession.builder.appName("InitCap Example").getOrCreate()

data = [("Apple", "red"),
        ("Banana", "Yellow"),
        ("hello", "world")]
columns = ["string1", "string2"]

df = spark.createDataFrame(data, columns)
capitalized_df = df.withColumn("string2_capitalized", initcap(col("string2")))
capitalized_df.show()

from pyspark.sql import SparkSession
from pyspark.sql.functions import regexp_replace, col

spark = SparkSession.builder.appName("Regexp Replace Example").getOrCreate()

data = [("Apple", "red"),
        ("Banana", "Yellow"),
        ("hello", "world")]
columns = ["string1", "string2"]

df = spark.createDataFrame(data, columns)
replaced_df = df.withColumn("string2_replaced", regexp_replace(col("string2"), "Electric", "EV"))
replaced_df.show()

from pyspark.sql import SparkSession
from pyspark.sql.functions import regexp_extract, col

spark = SparkSession.builder.appName("Regexp Extract Example").getOrCreate()

data = [("kia", "Electric car 2023"),
        ("BYD", "SUV 2021"),
        ("TATA", "Electric model 2022")]
columns = ["string1", "string2"]

df = spark.createDataFrame(data, columns)
extracted_df = df.withColumn("model_digits", regexp_extract(col("string2"), "([0-9]+)", 1))
extracted_df.show()

from pyspark.sql import SparkSession
from pyspark.sql.functions import encode, col

spark = SparkSession.builder.appName("Encode Example").getOrCreate()

data = [("kitten", "Electric car"),
        ("flaw", "SUV"),
        ("hello", "Electric model")]
columns = ["string1", "string2"]

df = spark.createDataFrame(data, columns)
encoded_df = df.withColumn("string2_encoded", encode(col("string2"), "UTF-8"))
encoded_df.show(truncate=False)

from pyspark.sql.functions import decode, col

decoded_df = encoded_df.withColumn("string2_decoded", decode(col("string2_encoded"), "UTF-8"))
decoded_df.show()

from pyspark.sql import SparkSession
from pyspark.sql.functions import format_number, col

spark = SparkSession.builder.appName("example").getOrCreate()

data = [("John", 3000), ("Jane", 4500), ("Jake", 5000)]
columns = ["name", "salary"]

df = spark.createDataFrame(data, columns)
formatted_df = df.withColumn("salary_formatted", format_number(col("salary").cast("double"), 4))
formatted_df.show()

from pyspark.sql.functions import format_string

data = [("Toyota Camry", "Sedan", "2022"),
        ("Honda Civic", "Sedan", "2022"),
        ("Ford F-150", "Truck", "2022"),
        ("Tesla Model 3", "Electric", "2022"),
        ("Chevrolet Malibu", "Sedan", "2022")]
columns = ["model", "type", "year"]

df = spark.createDataFrame(data, columns)
df.createOrReplaceTempView("cars")

formatted_string_df = df.withColumn(
    "formatted_details",
    format_string("%s (%s) - %s", col("model"), col("type"), col("year"))
)
formatted_string_df.show(truncate=False)

from pyspark.sql.functions import locate

position_df = df.withColumn("camry_position", locate("F", col("model")))
position_df.show()

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("PySpark_Date_Tim_Example").getOrCreate()

from pyspark.sql.functions import *

data=[["1","2020-02-01"],["2","2019-03-01"],["3","2021-03-01"]]
df=spark.createDataFrame(data,["id","input"])

df.select(current_date().alias("current_date")).show(1)

df.select(col("input"),date_format(col("input"), "MM-dd-yyyy").alias("date_format")).show()

df.select(col("input"),to_date(col("input"), "yyy-MM-dd").alias("to_date")).show()

df.select(col("input"), datediff(current_date(),col("input")).alias("datediff")).show()

df.select(col("input"),months_between(current_date(),col("input")).alias("months_between")).show()

df.select(col("input"),
          trunc(col("input"),"Month").alias("Month_Trunc"),
          trunc(col("input"),"Year").alias("Month_Year"),
          trunc(col("input"),"Month").alias("Month_Trunc")).show()

from pyspark.sql.functions import col, trunc
from pyspark.sql.types import StringType, StructType, StructField

data = [("2023-07-15",), ("2023-08-20",), ("2023-09-10",)]
schema = StructType([StructField("input", StringType(), True)])

df = spark.createDataFrame(data, schema)

result_df = df.select(
    col("input"),
    trunc(col("input"), "Month").alias("Month_Trunc"),
    trunc(col("input"), "Year").alias("Month_Year"),
    trunc(col("input"), "Month").alias("Month_Trunc_2")
)
result_df.show()

df.select(col("input"),
          year(col("input")).alias("year"),
          month(col("input")).alias("month"),
          next_day(col("input"),"Sunday").alias("next_day"),
          weekofyear(col("input")).alias("weekofyear") ).show()

df.select(col("input"),
     dayofweek(col("input")).alias("dayofweek"),
     dayofmonth(col("input")).alias("dayofmonth"),
     dayofyear(col("input")).alias("dayofyear"),
  ).show()

data=[["1","02-01-2020 11 01 19 06"],["2","03-01-2019 12 01 19 406"],["3","03-01-2021 12 01 19 406"]]
df2=spark.createDataFrame(data,["id","input"])
df2.show(truncate=False)

df2.select(current_timestamp().alias("current_timestamp")
  ).show(1,truncate=False)

df2.select(col("input"),
    to_timestamp(col("input"), "MM-dd-yyyy HH mm ss SSS").alias("to_timestamp")
  ).show(truncate=False)

data=[["1","2020-02-01 11:01:19.06"],["2","2019-03-01 12:01:19.406"],["3","2021-03-01 12:01:19.406"]]
df3=spark.createDataFrame(data,["id","input"])

df3.select(col("input"),
    hour(col("input")).alias("hour"),
    minute(col("input")).alias("minute"),
    second(col("input")).alias("second")
  ).show(truncate=False)""")
    
    elif(num == 7):
        print("""!pip install pyspark

from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("PySpark_WindowFunction_Example").getOrCreate()

simpleData = (("James", "Sales", 3000),
    ("Maria", "Finance", 3000),
    ("James", "Sales", 3000),
    ("Scott", "Finance", 3300),
    ("Jeff", "Marketing", 3000),
)

columns = ["employee_name", "department", "salary"]
df = spark.createDataFrame(data=simpleData, schema=columns)
df.printSchema()
df.show(truncate=False)

from pyspark.sql.window import Window
from pyspark.sql.functions import row_number
windowSpec = Window.partitionBy("department").orderBy("salary")

df.withColumn("row_number", row_number().over(windowSpec)).show(truncate=False)

from pyspark.sql.functions import rank
df.withColumn("rank", rank().over(windowSpec)).show()

from pyspark.sql.functions import dense_rank
df.withColumn("dense_rank", dense_rank().over(windowSpec)).show()

from pyspark.sql.functions import percent_rank
df.withColumn("percent_rank", percent_rank().over(windowSpec)).show()

from pyspark.sql.functions import ntile
df.withColumn("ntile", ntile(2).over(windowSpec)).show()

from pyspark.sql.functions import cume_dist
df.withColumn("cume_dist", cume_dist().over(windowSpec)).show()

from pyspark.sql.functions import lag
df.withColumn("lag", lag("salary", 2).over(windowSpec)).show()

from pyspark.sql.functions import lead
df.withColumn("lead", lead("salary", 2).over(windowSpec)).show()

windowSpecAgg = Window.partitionBy("department")
from pyspark.sql.functions import col, avg, sum, min, max, row_number
df.withColumn("row", row_number().over(windowSpec)) \
    .withColumn("avg", avg(col("salary")).over(windowSpecAgg)) \
    .withColumn("sum", sum(col("salary")).over(windowSpecAgg)) \
    .withColumn("min", min(col("salary")).over(windowSpecAgg)) \
    .withColumn("max", max(col("salary")).over(windowSpecAgg)) \
    .where(col("row") == 1).select("department", "row", "avg", "sum", "min", "max") \
    .show()

df.withColumn("row", row_number().over(windowSpec)) \
    .withColumn("avg", avg(col("salary")).over(windowSpecAgg)) \
    .withColumn("sum", sum(col("salary")).over(windowSpecAgg)) \
    .withColumn("min", min(col("salary")).over(windowSpecAgg)) \
    .withColumn("max", max(col("salary")).over(windowSpecAgg)) \
    .show()

windowSpecAgg = Window.partitionBy("department")
from pyspark.sql.functions import col, avg, sum, min, max, row_number
df.withColumn("row", row_number().over(windowSpec)) \
    .withColumn("avg", avg(col("salary")).over(windowSpecAgg)) \
    .show()""")
    
    elif(num == 9):
        print("""!pip install pyspark

from pyspark.ml.tuning import ParamGridBuilder, CrossValidator
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.classification import LogisticRegression
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("HyperparameterTuningExample").getOrCreate()

filepath = "/content/houseprice.csv"
df1 = spark.read.csv(filepath, header=True)
df1.show()
print(type(df1))

df1.select("country", "price").show(5)

from pyspark.sql import types as t
from pyspark.sql import functions as f

cdf1 = df1.withColumn("price", f.when(f.col("price") > 600000, "high").otherwise("low"))
print(type(cdf1))

cdf1.show(5)
cdf1.select("country", "price").show(5)
cdf1.groupBy("price").count().show()

from pyspark.sql.types import IntegerType, StringType

cdf1 = cdf1.withColumn("bathrooms", cdf1["bathrooms"].cast(IntegerType()))
cdf1 = cdf1.withColumn("bedrooms", cdf1["bedrooms"].cast(IntegerType()))
cdf1 = cdf1.withColumn("sqft_living", cdf1["sqft_living"].cast(IntegerType()))
cdf1 = cdf1.withColumn("sqft_lot", cdf1["sqft_lot"].cast(IntegerType()))
cdf1 = cdf1.withColumn("floors", cdf1["floors"].cast(IntegerType()))
cdf1 = cdf1.withColumn("sqft_basement", cdf1["sqft_basement"].cast(IntegerType()))
cdf1.printSchema()

print(type(df1))

(train_df1, test_df1) = cdf1.randomSplit([0.8, 0.2], 11)
print("Number of train samples: " + str(train_df1.count()))
print("Number of test samples: " + str(test_df1.count()))

from pyspark.ml.feature import StringIndexer

price_indexer = StringIndexer(inputCol="price", outputCol="price_index")
print(price_indexer)

price_indexed_df1 = price_indexer.fit(train_df1)
print(price_indexed_df1)

train_df1 = price_indexed_df1.transform(train_df1)
train_df1.show()

from pyspark.ml.feature import VectorAssembler

inputCols = ['bedrooms', 'bathrooms', 'sqft_living', 'sqft_lot', 'floors', 'sqft_basement']
outputCol = "features"

vector_assembler = VectorAssembler(inputCols=inputCols, outputCol=outputCol)
train_df1 = vector_assembler.transform(train_df1)
train_df1.show(5)

modeling_df = train_df1.select(['features', 'price_index'])
modeling_df.show(20, truncate=False)

from pyspark.ml.tuning import ParamGridBuilder, CrossValidator
from pyspark.ml.classification import LogisticRegression

lr = LogisticRegression(labelCol="price_index", featuresCol="features")

from pyspark.ml.evaluation import MulticlassClassificationEvaluator

evaluator = MulticlassClassificationEvaluator(labelCol="price_index")

param_grid = (ParamGridBuilder()
              .addGrid(lr.regParam, [0.01, 0.1, 1.0])
              .addGrid(lr.elasticNetParam, [0.0, 0.5, 1.0])
              .build())

crossval = CrossValidator(estimator=lr,
                          estimatorParamMaps=param_grid,
                          evaluator=evaluator,
                          numFolds=3)

cv_model = crossval.fit(train_df1)

price_indexer = StringIndexer(inputCol="price", outputCol="price_index")
price_indexed_df1 = price_indexer.fit(test_df1)
test_df1 = price_indexed_df1.transform(test_df1)
test_df1.show()
test_df1.printSchema()

test_df1 = vector_assembler.transform(test_df1)

cv_model = crossval.fit(test_df1)""")
        
    elif(num == 10):
        print("""!pip install pyspark

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Example").getOrCreate()

filepath = "/content/houseprice.csv"
df = spark.read.format('csv').options(header='true', inferSchema='true', delimiter=';').load(filepath)
df.show(5, truncate=False)
df.printSchema()

print(type(df))

df1 = spark.read.csv(filepath, header=True)
df1.show()
print(type(df1))

df1.select("country", "price").show(5)

from pyspark.sql import types as t
from pyspark.sql import functions as f

cdf1 = df1.withColumn("price", f.when(f.col("price") > 600000, "high").otherwise("low"))
print(type(cdf1))

cdf1.show(5)
cdf1.select("country", "price").show(5)
cdf1.groupBy("price").count().show()

from pyspark.sql.types import IntegerType, StringType

cdf1 = cdf1.withColumn("bathrooms", cdf1["bathrooms"].cast(IntegerType()))
cdf1 = cdf1.withColumn("bedrooms", cdf1["bedrooms"].cast(IntegerType()))
cdf1 = cdf1.withColumn("sqft_living", cdf1["sqft_living"].cast(IntegerType()))
cdf1 = cdf1.withColumn("sqft_lot", cdf1["sqft_lot"].cast(IntegerType()))
cdf1 = cdf1.withColumn("floors", cdf1["floors"].cast(IntegerType()))
cdf1 = cdf1.withColumn("sqft_basement", cdf1["sqft_basement"].cast(IntegerType()))
cdf1.printSchema()

(train_df1, test_df1) = cdf1.randomSplit([0.8, 0.2], 11)
print("Number of train samples: " + str(train_df1.count()))
print("Number of test samples: " + str(test_df1.count()))

from pyspark.ml.feature import StringIndexer

price_indexer = StringIndexer(inputCol="price", outputCol="price_index")
price_indexed_df1 = price_indexer.fit(train_df1)
print(price_indexed_df1)

train_df1 = price_indexed_df1.transform(train_df1)
train_df1.show()

from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import DecisionTreeClassifier

inputCols = ['bedrooms', 'bathrooms', 'sqft_living', 'sqft_lot', 'floors', 'sqft_basement']
outputCol = "features"

vector_assembler = VectorAssembler(inputCols=inputCols, outputCol=outputCol)
train_df1 = vector_assembler.transform(train_df1)
train_df1.show(5)

modeling_df = train_df1.select(['features', 'price_index'])

dt_model = DecisionTreeClassifier(labelCol="price_index", featuresCol="features")
dt_model = dt_model.fit(modeling_df)

predictions = dt_model.transform(modeling_df)
predictions.show(20, truncate=False)

from pyspark.ml.tuning import ParamGridBuilder, CrossValidator

from pyspark.ml.evaluation import MulticlassClassificationEvaluator

evaluatorDT = MulticlassClassificationEvaluator(labelCol="price_index")

price_indexer = StringIndexer(inputCol="price", outputCol="price_index")
price_indexed_df1 = price_indexer.fit(test_df1)
test_df1 = price_indexed_df1.transform(test_df1)
test_df1.show()
test_df1.printSchema()

test_df1 = vector_assembler.transform(test_df1)
test_predictions = dt_model.transform(test_df1)
test_predictions.show(20, truncate=False)

area_under_curve = evaluatorDT.evaluate(test_predictions)
area_under_curve

from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.classification import DecisionTreeClassifier
from pyspark.sql import SparkSession
from pyspark.sql.types import IntegerType
import pyspark.sql.functions as F
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

spark = SparkSession.builder.appName("HousePriceClassification").getOrCreate()

filepath = "/content/houseprice.csv"
df = spark.read.csv(filepath, header=True, inferSchema=True)

df = df.withColumn("price", F.when(F.col("price") > 600000, 1).otherwise(0).cast(IntegerType()))

int_columns = ['bathrooms', 'bedrooms', 'sqft_living', 'sqft_lot', 'floors', 'sqft_basement']
for col_name in int_columns:
    df = df.withColumn(col_name, df[col_name].cast(IntegerType()))

train_df, test_df = df.randomSplit([0.8, 0.2], seed=11)

price_indexer = StringIndexer(inputCol="price", outputCol="price_index")
train_df = price_indexer.fit(train_df).transform(train_df)

input_cols = ['bedrooms', 'bathrooms', 'sqft_living', 'sqft_lot', 'floors', 'sqft_basement']
vector_assembler = VectorAssembler(inputCols=input_cols, outputCol="features")
train_df = vector_assembler.transform(train_df)

dt_model = DecisionTreeClassifier(labelCol="price_index", featuresCol="features")
dt_model = dt_model.fit(train_df)

evaluator = MulticlassClassificationEvaluator(labelCol="price_index")

test_df = test_df.withColumn("price", F.when(F.col("price") > 600000, 1).otherwise(0).cast(IntegerType()))
test_df = price_indexer.fit(test_df).transform(test_df)
test_df = vector_assembler.transform(test_df)
test_predictions = dt_model.transform(test_df)

area_under_curve = evaluator.evaluate(test_predictions)
print(f"Area under ROC curve: {area_under_curve}")

from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.classification import DecisionTreeClassifier
from pyspark.sql import SparkSession
from pyspark.sql.functions import when
from pyspark.sql.types import IntegerType
import pyspark.sql.functions as F

spark = SparkSession.builder.appName("YourAppName").getOrCreate()

filepath = "/content/houseprice.csv"
df1 = spark.read.csv(filepath, header=True)

df1 = df1.withColumn("price", when(F.col("price") > 600000, 1).otherwise(0).cast(IntegerType()))

inputColumns = ['bedrooms', 'bathrooms', 'sqft_living', 'sqft_lot', 'floors', 'sqft_basement']
outputColumn = "features"

for col_name in inputColumns:
    df1 = df1.withColumn(col_name, df1[col_name].cast(IntegerType()))

price_indexer = StringIndexer(inputCol="price", outputCol="priceIndex")

vector_assembler = VectorAssembler(inputCols=inputColumns, outputCol=outputColumn)

dt_model = DecisionTreeClassifier(labelCol="price", featuresCol=outputColumn)

stages = [price_indexer, vector_assembler, dt_model]

pipeline = Pipeline(stages=stages)

(train_df2, test_df2) = df1.randomSplit([0.8, 0.2], seed=11)

final_pipeline = pipeline.fit(train_df2)

test_predictions_from_pipeline = final_pipeline.transform(test_df2)

test_predictions_from_pipeline.select("price", "prediction").show(5)

from pyspark.ml.evaluation import MulticlassClassificationEvaluator

evaluator = MulticlassClassificationEvaluator(labelCol="price", predictionCol="prediction", metricName="accuracy")

accuracy = evaluator.evaluate(test_predictions_from_pipeline)
print(f"Accuracy: {accuracy}")""")


def main():
    """
    Main entry point for the command-line interface.
    """
    import sys
    
    if len(sys.argv) < 2:
        print("MrPrince - PySpark Code Snippets Library")
        print("\nUsage: mrprince <category_number>")
        print("\nAvailable categories:")
        print("  1: RDD Operations")
        print("  2: DataFrame Operations")
        print("  3: Filtering and Grouping")
        print("  4: File Operations")
        print("  5: SQL Operations")
        print("  6: String Functions")
        print("  7: Window Functions")
        print("  9: Hyperparameter Tuning")
        print("  10: ML Pipelines")
        print("\nExample: mrprince 1")
        sys.exit(1)
    
    try:
        category = int(sys.argv[1])
        program(category)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
