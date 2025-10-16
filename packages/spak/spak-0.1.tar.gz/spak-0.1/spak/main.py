def q1():
    print("""
# Install PySpark
!pip install pyspark

# ------------------ SparkSession ------------------
from pyspark.sql import SparkSession
spark = SparkSession.builder.master("local[2]").appName("SparkByExamples.com").getOrCreate()

# ------------------ Create RDD ------------------
sc = spark.sparkContext
data = [1,2,3,4,5,6,7,8,9,10,11,12]
rdd = sc.parallelize(data)

# ------------------ Actions ------------------
print(rdd.count())          # count()
print(rdd.collect())        # collect()
print(rdd.first())          # first()
print(rdd.take(5))          # take()

# ------------------ reduce() ------------------
print(rdd.reduce(lambda x, y: x + y))

# ------------------ saveAsTextFile ------------------
save_rdd = sc.parallelize([1,2,3,4,5,6], numSlices=5)
save_rdd.saveAsTextFile('file3.txt')

# ------------------ takeSample() ------------------
rdd = spark.sparkContext.parallelize([1, 1, 3, 2, 4,5,6,8])
sample_with_replacement = rdd.takeSample(True, 5, seed=42)
sample_without_replacement = rdd.takeSample(False, 5, seed=42)
print("Sample with replacement:", sample_with_replacement)
print("Sample without replacement:", sample_without_replacement)

# ------------------ takeOrdered() ------------------
rdd = spark.sparkContext.parallelize([10, 4, 2, 7, 3, 6, 9, 8, 1, 5])
print("Smallest 5 elements:", rdd.takeOrdered(5))
print("Largest 5 elements:", rdd.takeOrdered(5, key=lambda x: -x))

# ------------------ saveAsSequenceFile() ------------------
rdd = spark.sparkContext.parallelize([("key1", 5), ("key2", 4), ("key3", 3)])
rdd.saveAsSequenceFile("sequence_file-1")

# Read Sequence File
spark.conf.set("dfs.checksum.enabled", "false")
rdd = spark.sparkContext.sequenceFile("sequence_file-1")
print(rdd.collect())

# ------------------ saveAsPickleFile() ------------------
rdd = spark.sparkContext.parallelize([("key1", 1), ("key2", 2), ("key3", 3)])
rdd.saveAsPickleFile("pickle-file")

# Read Pickle File
rdd = spark.sparkContext.pickleFile("pickle-file")
print(rdd.collect())

# ------------------ countByKey() ------------------
rdd = spark.sparkContext.parallelize([("a", 1), ("b", 1), ("a", 2), ("b", 3), ("b", 4)])
print(rdd.countByKey())

# ------------------ foreach() ------------------
rdd = spark.sparkContext.parallelize([1, 2, 3, 4, 5])
for element in rdd.collect():
    print(f"Element: {element}")

# ------------------ Transformations ------------------
# map()
my_rdd = sc.parallelize([1,2,3,4])
print(my_rdd.map(lambda x: x + 10).collect())

# filter()
filter_rdd = sc.parallelize([2, 3, 4, 5, 6, 7])
print(filter_rdd.filter(lambda x: x % 2 == 0).collect())

filter_rdd_2 = sc.parallelize(['Rahul', 'Swati', 'Rohan', 'Shreya', 'Priya'])
print(filter_rdd_2.filter(lambda x: x.startswith('R')).collect())

# union()
union_inp = sc.parallelize([2,4,5,6,7,8,9])
union_rdd_1 = union_inp.filter(lambda x: x % 2 == 0)
union_rdd_2 = union_inp.filter(lambda x: x % 3 == 0)
print(union_rdd_1.union(union_rdd_2).collect())

# intersection()
inp = sc.parallelize([1,2,4,5,6,7,8,9,10,11,12,13,14,15,16,18,19,20])
rdd_1 = inp.filter(lambda x: x % 2 == 0)
rdd_2 = inp.filter(lambda x: x % 3 == 0)
print(rdd_1.intersection(rdd_2).collect())

# subtract()
inp = sc.parallelize([1,2,4,5,6,7,8,9,10])
rdd_1 = inp.filter(lambda x: x % 2 == 0)
rdd_2 = inp.filter(lambda x: x % 3 == 0)
print(rdd_1.subtract(rdd_2).collect())

# flatMap()
flatmap_rdd = sc.parallelize(["Hey there", "This is PySpark RDD Transformations"])
print(flatmap_rdd.flatMap(lambda x: x.split(" ")).collect())

# mapValues()
pair_rdd = sc.parallelize([(1, 'apple'), (2, 'banana'), (1, 'orange'), (2, 'grape')])
def append_fruit(value): return value + " fruit"
modified_rdd = pair_rdd.mapValues(append_fruit)
print(modified_rdd.collect())

# ------------------ Pair RDD Operations ------------------
marks = [('Rahul', 88), ('Swati', 92), ('Shreya', 83), ('Abhay', 93), ('Rohan', 78)]
print(sc.parallelize(marks).collect())

# reduceByKey()
marks_rdd = sc.parallelize([
    ('Rahul', 25), ('Swati', 26), ('Shreya', 22), ('Abhay', 29), ('Rohan', 22),
    ('Rahul', 23), ('Swati', 19), ('Shreya', 28), ('Abhay', 26), ('Rohan', 22)
])
print(marks_rdd.reduceByKey(lambda x, y: x + y).collect())

# sortByKey()
print(marks_rdd.sortByKey(ascending=True).collect())

# groupByKey()
dict_rdd = marks_rdd.groupByKey().collect()
for key, value in dict_rdd:
    print(key, list(value))

# countByKey()
marks_rdd = sc.parallelize([
    ('Rahul', 25), ('Swati', 26), ('Rohan', 22),
    ('Rahul', 23), ('Swati', 19), ('Shreya', 28),
    ('Abhay', 26), ('Rohan', 22)
])
dict_rdd = marks_rdd.countByKey().items()
for key, value in dict_rdd:
    print(key, value)

spark.stop()
""")


def q2():
    print("""
# ===============================================
# 📘 PySpark – Data Processing from Different Data Sources
# ===============================================

# Install PySpark
!pip install pyspark

# Import
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
from pyspark.sql.functions import max

# ------------------------------------------------------------
# 1️⃣ Initialize Spark Session
# ------------------------------------------------------------
spark = SparkSession.builder.appName("Data Processing Pipeline").getOrCreate()

# ------------------------------------------------------------
# 2️⃣ Read CSV Data
# ------------------------------------------------------------
df = spark.read.csv("/content/healthcare_dataset.csv", header=True, inferSchema=False)

# Display first 20 rows
df.show()

# Check DataFrame type
print("DataFrame type:", type(df))

# Display selected columns
df.select(df['Patient_ID'], df['Age']).show(15)
df.select(df['Patient_ID'], df['Blood_Pressure']).show(25)

# Show datatypes
print("Column DataTypes:")
print(df.dtypes)

# ------------------------------------------------------------
# 3️⃣ Define Custom Schema with StructType
# ------------------------------------------------------------
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
    (1, "Alice", ("123 Main St", "Springfield", "12345")),
    (2, "Bob", ("456 Elm St", "Shelbyville", "67890"))
]

df_struct = spark.createDataFrame(data, schema)
print("\\nStructured DataFrame:")
df_struct.show(truncate=False)
print("Schema with nested struct:")
print(df_struct.dtypes)

# ------------------------------------------------------------
# 4️⃣ Nullable vs Non-Nullable Fields
# ------------------------------------------------------------
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

print("\\nDataFrame with Nullable Fields:")
df_nullable.show()

print("\\nDataFrame with Non-Nullable Fields:")
df_non_nullable.show()

# ------------------------------------------------------------
# 5️⃣ Read CSV with custom separator
# ------------------------------------------------------------
df_sep = spark.read.csv("/content/csv_seperator_file.csv", sep='@', header=True, inferSchema=True)
print("\\nCSV with Custom Separator:")
df_sep.show()

# Write DataFrame to CSV
df_sep.write.csv("/content/processing1.csv")
df_sep.write.format("csv").mode('overwrite').save("/content/res")

# ------------------------------------------------------------
# 6️⃣ Read text file
# ------------------------------------------------------------
df_text = spark.read.text("/content/s1.txt")
print("\\nText File DataFrame:")
df_text.show(truncate=False)
print("DataFrame type:", type(df_text))

# ------------------------------------------------------------
# 7️⃣ Read JSON File
# ------------------------------------------------------------
json_path = "/content/iris1.json"
df_json = spark.read.json(json_path)
print("\\nJSON File Schema:")
df_json.printSchema()

# ------------------------------------------------------------
# 8️⃣ Process Another CSV (London Dataset)
# ------------------------------------------------------------
df_london = spark.read.csv("/content/London.csv", header=True, inferSchema=True)

# Drop column
cols_to_drop = ['Postal Code']
df_london = df_london.drop(*cols_to_drop)

# Display data
df_london.show()
print("Total Records:", df_london.count())

# Select Columns
df_london.select(df_london["Property Name"], df_london["Price"]).show(5)

# Filter Examples
df_london.filter(df_london["Property Name"] == "Queens Road").show()
df_london.filter(
    (df_london["Property Name"] == "Hornton Street") &
    (df_london["House Type"] == "Flat / Apartment") &
    (df_london["Area in sq ft"] == 646)
).show()

df_london.filter(
    (df_london["Property Name"] == "Hornton Street") |
    (df_london["House Type"] == "Flat / Apartment") |
    (df_london["Area in sq ft"] > 646)
).show()

# Order Data
df_london.orderBy(df_london["Property Name"].asc(), df_london["Location"].desc()).show(5, truncate=False)

# Grouping & Aggregation
df_london.groupBy("Property Name").sum("Area in sq ft").show()
df_london.groupBy("Price").count().show(50)

# Max Price
df_london.select(max("Price")).show(truncate=False)

# ------------------------------------------------------------
# ✅ Done
# ------------------------------------------------------------
print("\\n✅ Data Processing from Multiple Data Sources Completed Successfully!")
""")
def q3():
    print("""
# EXPERIMENT 3 – PYSPARK DATAFRAMES

# Step 1: Install and import
# (In Colab: !pip install pyspark)
from pyspark.sql import SparkSession
from pyspark.sql.functions import sum, avg, max, col

# Step 2: Create Spark session
spark = SparkSession.builder.appName("sparkdataframes").getOrCreate()

# Step 3: Sample Employee Data
data = [
    (1, "aravind", "DataAnalyst", 28000, "Rahul"),
    (2, "Banu", "Analyst", 22000, "Vetri"),
    (3, "Cibi", "Manager", 35000, "Swetha"),
    (4, "Rithu", "Manager", 35000, "Ram"),
    (5, "Hari", "Manager", 35000, "kumar"),
    (6, "Devi", "Engineer", 3000, "Nalini")
]
columns = ["Empid", "EMP_NAME", "POSITION", "SALARY", "Manager"]

df = spark.createDataFrame(data, columns)

# Step 4: Display data and schema
df.show()
df.printSchema()

# Step 5: Display limited rows
df.show(n=2, truncate=25)
df.show(n=3, truncate=2)

# Step 6: Select all and subset of columns
df.select("*").show()
df.select(df.columns[1:4]).show(3)

# Step 7: Collect data
print(df.collect())

# Step 8: Filter operations
df.filter(df.Manager == "kumar").show(truncate=False)
df.filter(~(df.Manager == "kumar")).show(truncate=False)
df.filter(df.Manager != "kumar").show()
df.filter("Manager <> 'kumar'").show()
df.filter((df.POSITION == "Manager") & (df.Empid == "4")).show()
df.filter((df.POSITION == "Manager") | (df.Empid == "4")).show()

# Step 9: Using isin()
list1 = ["Nalini", "Rahul", "Vetri"]
df.filter(df.Manager.isin(list1)).show()
list2 = ["Nalini", "Rahul"]
df.filter(df.Manager.isin(list2)).show(truncate=3)
df.filter(df.Manager.isin(list1) == False).show()
df.filter(df.Manager.isin(list1) == True).show()

# Step 10: String filters
df.filter(df.EMP_NAME.startswith("B")).show()
df.filter(df.EMP_NAME.endswith("u")).show()
df.filter(df.EMP_NAME.contains("h")).show()

# Step 11: LIKE operations
df.filter(df.POSITION.like("D%")).show()
df.filter(df.POSITION.like("%t")).show()
df.filter(df.POSITION.like("%a%")).show()
df.filter(df.POSITION.like("%i%")).show()

# Step 12: Sorting
df.sort("EMP_NAME").show()
df.sort("Empid", "EMP_NAME").show()
df.orderBy("SALARY", "Empid").show()
df.sort(df.POSITION.asc(), df.Empid.asc()).show()
df.sort(df.POSITION.desc(), df.EMP_NAME.asc()).show()

# Step 13: New dataset - customerdata
customerdata = [
    (1, "ABi", 9089078901, "Tamilnadu", 18, 3245),
    (2, "william", 889078901, "Kerala", 28, 111),
    (3, "xavier", 789078901, "Karnataka", 38, 121),
    (4, "john", 9012078901, "Tamilnadu", 48, 123),
    (5, "chitu", 9089078934, "Andhra", 58, 111),
    (6, "saran", 9089078661, "Madya", 18, 444),
    (7, "prave", 96789000001, "Jammu", 23, 555),
    (8, "parvathy", 9089700901, "Goa", 24, 666),
    (9, "xena", 90780078901, "Punjab", 33, 777),
    (10, "Haier", 912349078901, "Srilanka", 36, 8888),
    (11, "UUII", 9089078901, "Rajasthan", 17, 9000),
    (12, "Zenith", 9089078901, "Gujarat", 16, 1234),
    (13, "ABirami", 9089078901, "Uttra Pradesh", 10, 1112),
    (14, "preetha", 9089078901, "Tamilnadu", 8, 3245)
]

schema = ["Id", "Name", "Phone", "state", "age", "cost"]
df = spark.createDataFrame(customerdata, schema)
df.printSchema()
df.show(truncate=False)

# Step 14: GroupBy operations
df.groupBy("state").sum("cost").show()
df.groupBy("state").count().show()
df.groupBy("state").min("cost").show()
df.groupBy("state").max("cost").show()
df.groupBy("state").avg("cost").show()
df.groupBy("state").mean("cost").show()
df.groupBy("state", "age").sum("cost").show()

# Step 15: Using agg() function
df.groupBy("state").agg(sum("cost")).show()
df.groupBy("state").agg(
    sum("cost").alias("sum_cost"),
    avg("cost").alias("avg_cost"),
    max("cost").alias("max_cost")
).show()

# Step 16: Filter aggregated data
df.groupBy("state").agg(
    sum("cost").alias("sum_cost"),
    avg("cost").alias("avg_cost"),
    max("cost").alias("max_cost")
).where(col("sum_cost") >= 1000).show()

# Step 17: Show max cost
df.select(max("cost")).show()

# Stop Spark
spark.stop()
""")
def q4():
    print("""
!pip install pyspark
import pandas as pd
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import max, min, col, split
from pyspark.sql.window import Window

# ---------------------- PART 1 ----------------------
spark = SparkSession.builder.appName("Temperature").getOrCreate()
sc = spark.sparkContext
lines = sc.textFile("/content/weather2.csv")
lines2 = spark.read.csv("/content/weather2.csv")
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

# ---------------------- PART 2 ----------------------
spark = SparkSession.builder.appName("MaxTemperature").getOrCreate()
weather_df = spark.read.csv("/content/weather1.csv", header=True, inferSchema=True)
max_temp_value = weather_df.select(max("MaxTemp").alias("MaxTemperature")).collect()[0]["MaxTemperature"]
max_temp_row = weather_df.filter(col("MaxTemp") == max_temp_value)
max_temp_row.show()
max_temp_cities = max_temp_row.select("state")
max_temp_cities.show()

# ---------------------- PART 3 ----------------------
spark = SparkSession.builder.appName("CompareTemperature").getOrCreate()
csv_df = spark.read.csv("/content/weather1.csv", header=True, inferSchema=True).select("State", "MaxTemp")
print("CSV file")
csv_df.show()

text_df = spark.read.text("/content/weather1.txt")
header = text_df.first()[0]
data_df = text_df.filter(text_df["value"] != header)
text_df1 = data_df.select(
    split(col("value"), ",")[0].alias("State"),
    split(col("value"), ",")[1].cast("double").alias("MaxTemp")
)
print("Text file")
text_df1.show()

json_df = spark.read.json("/content/weather1.json")
json_clean_df = json_df.select("State", "MaxTemp").filter(col("State").isNotNull())
print("JSON file")
json_clean_df.show()

tsv_df = spark.read.csv("/content/weather1.tsv", sep="\t", header=True, inferSchema=True).select("State", "MaxTemp")
print("TSV file")
tsv_df.show()

pandas_df = pd.read_excel("/content/weather1.xlsx")
xlsx_df = spark.createDataFrame(pandas_df).select("state", "MaxTemp")
print("XLSX file")
xlsx_df.show()

list_data = [
    ("Tamil Nadu", 34),
    ("Maharashtra", 36),
    ("Gujarat", 38),
    ("Kerala", 33),
    ("Punjab", 40)
]
list_df = spark.createDataFrame(list_data, ["State", "MaxTemp"])
print("List file")
list_df.show()

combined_df = csv_df.union(json_clean_df).union(tsv_df).union(list_df).union(xlsx_df).union(text_df1)
print("Combined DataFrames")
combined_df.show()

min_temp_df = combined_df.groupBy("State").agg(min("MaxTemp").alias("MinTemperature"))
min_temp_df.show()
spark.stop()

# ---------------------- PART 4 ----------------------
spark = SparkSession.builder.appName("SQL_Min_Temp").getOrCreate()
df = spark.read.option("header", "true").option("inferSchema", "true").csv("/content/weather1.csv")
df.createOrReplaceTempView("weather")
min_temp_df = spark.sql(\"\"\"
    SELECT State, MIN(MaxTemp) AS MinTemperature
    FROM weather
    GROUP BY State
\"\"\")
min_temp_df.show()

folder_path = "/content/Min_temp Folder"
os.makedirs(folder_path, exist_ok=True)
print(f"Folder created at: {folder_path}")

# ---------------------- PART 5 ----------------------
spark = SparkSession.builder.appName("MinTemperature").getOrCreate()
csv_folder_path = "/content/weather2.csv"
df = spark.read.option("header", "true").csv(csv_folder_path)
print("CSV Folder Values:")
df.show()
print(df.columns)
min_temp_df = df.groupBy("state").agg(min(col("MinTemp")).alias("MinTemperature"))
min_temp_df.show()

# ---------------------- PART 6 ----------------------
spark = SparkSession.builder.appName("MinTemp_Window").getOrCreate()
df = spark.read.option("header", "true").option("inferSchema", "true").csv("/content/weather2.csv")
windowSpec = Window.partitionBy("state")
df_with_min = df.withColumn("MinTemperature", min(col("MinTemp")).over(windowSpec))
result_df = df_with_min.select("state", "MinTemperature").distinct()
result_df.show()
""")
def q5():
    print("""
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import lit, expr, when, col

# -------------------- Create SparkSession --------------------
spark = SparkSession.builder.appName("MySparkApp").enableHiveSupport().getOrCreate()

# -------------------- Create Sample Data --------------------
data = [
    (201, "Laptop", "Electronics", 2, 75000, "2025-08-01"),
    (202, "Shoes", "Fashion", 5, 3000, "2025-08-02"),
    (203, "Microwave", "Home Appliances", 1, 12000, "2025-08-03"),
    (204, "T-shirt", "Fashion", 10, 800, "2025-08-04")
]
columns = ["order_id", "product", "category", "quantity", "price", "order_date"]
df = spark.createDataFrame(data, columns)
df.show()
print(type(df))

# -------------------- SQL Table Operations --------------------
df.createOrReplaceTempView("sales")
result = spark.sql("SELECT * FROM sales")
result.show()

result = spark.sql("SELECT * FROM sales WHERE price < 5000")
result.show()

df.write.saveAsTable("newf_table")
df.printSchema()

spark.sql("DESCRIBE sales").show()
spark.sql("SHOW COLUMNS FROM sales").show()

# -------------------- Add New Column --------------------
df = df.withColumn("new_column", lit("sample_value"))
df.show()
spark.sql("DESCRIBE sales").show()

# -------------------- Insert Into Hive Table --------------------
spark.sql(\"\"\"
INSERT INTO newf_table VALUES
(201, "Laptop", "Electronics", 2, 75000, "2025-08-01"),
(202, "Shoes", "Fashion", 5, 3000, "2025-08-02"),
(203, "Microwave", "Home Appliances", 1, 12000, "2025-08-03"),
(204, "T-shirt", "Fashion", 10, 800, "2025-08-04")
\"\"\")

spark.sql("SELECT * FROM newf_table").show()

df = spark.read.table("newf_table")
df.show()

# -------------------- Add Derived Columns --------------------
updated_df = df.withColumn("discounted_price", expr("price - 500"))
updated_df.show()

df.write.mode("overwrite").format("parquet").saveAsTable("restaurant")
spark.sql("SHOW TABLES").show()
spark.sql("DESCRIBE restaurant").show()

updated_df = df.withColumn("price", expr("price + 1"))
updated_df.show()

updated_df = df.withColumn("Good_Score", when(df["price"] <= 8000, "Yes").otherwise("No"))
updated_df.show()

updated_df = df.filter(df['product'] != 'Shoes')
updated_df.show()

update_condition = (col("product") == "Shoes")
updated_df = df.withColumn("price", when(update_condition, 3500).otherwise(col("price")))
updated_df.show()

print("Sorted by price (descending):")
df.orderBy(col("price").desc()).show()

pass_df = df.withColumn(
    "status",
    when(col("price") >= 10000, lit("good")).otherwise(lit("bad"))
)
pass_df.show()

# -------------------- EXTRA 6 DDL & DML OPERATIONS --------------------
data = [
    (1, "Alice", "HR", 50000, "2022-01-15"),
    (2, "Bob", "IT", 60000, "2021-11-23"),
    (3, "Charlie", "Finance", 55000, "2023-03-10"),
    (4, "David", "IT", 65000, "2020-07-19"),
    (5, "Eva", "HR", 52000, "2022-09-05")
]
columns = ["emp_id", "name", "department", "salary", "joining_date"]
df = spark.createDataFrame(data, columns)

# Create Database and Table
spark.sql("CREATE DATABASE IF NOT EXISTS company_db")
df.write.saveAsTable("company_db.employees", format="parquet", mode="overwrite")
spark.sql("SELECT * FROM company_db.employees").show()

spark.sql("SHOW TABLES").show()

spark.sql("CREATE TABLE employees_copy AS SELECT * FROM employees")
spark.sql("SHOW TABLES").show()
spark.sql("DESCRIBE employees_copy").show()

spark.sql("ALTER TABLE employees_copy RENAME TO emp_copy")
spark.sql("SHOW TABLES").show()

spark.sql("DROP TABLE IF EXISTS emp_copy")
spark.sql("SHOW TABLES").show()

# -------------------- DML Operations --------------------
spark.sql(\"\"\"
INSERT INTO employees VALUES
(5, 'Eve', 'Finance', 60000, '2022-05-10'),
(6, 'Sam', 'Sales', 55000, '2023-03-15')
\"\"\")
spark.sql("SELECT * FROM employees").show()

spark.sql(\"\"\"
INSERT INTO employees VALUES
(6, 'Frank', 'IT', 72000, '2023-08-01')
\"\"\")
spark.sql("SELECT * FROM employees").show()

emp_df = spark.table("employees")

spark.sql("TRUNCATE TABLE employees")
spark.sql("SELECT * FROM employees").show()
""")
def q6():
    print("""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *

# =============================
# 🔹 STRING FUNCTIONS SECTION
# =============================

spark = SparkSession.builder.appName("String_Functions_Students").getOrCreate()

# Sample Student Data
data = [
    ("ST001", "Kiran Kumar", "Bangalore"),
    ("ST002", "Meera Nair", "Chennai"),
    ("ST003", "Arjun Reddy", "Hyderabad"),
    ("ST004", "Sita Devi", "Mumbai")
]
columns = ["StudentID", "Name", "City"]

df = spark.createDataFrame(data, columns)
df.show(truncate=False)

# String Operations
df.select(concat_ws("-", "StudentID","Name","City").alias("concat_ws")).show()
df.select("Name", substring("Name", 1, 5).alias("Substring")).show()
df.select("Name", instr("Name","a").alias("Instr")).show()
df.select(trim("Name").alias("Trimmed")).show()
df.select(upper("Name").alias("Upper")).show()
df.select(lower("Name").alias("Lower")).show()
df.select(initcap("Name").alias("Initcap")).show()
df.select(regexp_replace("City","a","@").alias("RegexpReplace")).show()
df.select(regexp_extract("City","[A-Za-z]+",0).alias("RegexpExtract")).show()
df.select(split("City"," ").alias("Split")).show()

# Extra String Functions
df.select(concat("Name", lit(" - Student")).alias("Concat")).show()
df.select(lpad("StudentID",6,"0").alias("LPAD")).show()
df.select(rpad("StudentID",6,"0").alias("RPAD")).show()

# Additional String Operations
df.select(reverse("Name").alias("Reversed")).show()
df.select(repeat("Name",2).alias("Repeated")).show()
df.select("Name", ascii(substring("Name",1,1)).alias("ASCII")).show()
df.select("City", locate("o","City").alias("Locate_Pos")).show()

# =============================
# 🔹 DATE-TIME FUNCTIONS SECTION
# =============================

spark = SparkSession.builder.appName("DateTime_Functions").getOrCreate()

# Employee Data
data = [
    ("EMP001", "Karthik", "2023-01-10"),
    ("EMP002", "Priya", "2022-05-18"),
    ("EMP003", "Rohit", "2021-12-01"),
    ("EMP004", "Sneha", "2020-07-22")
]
columns = ["EmpID", "Name", "JoinDate"]

df = spark.createDataFrame(data, columns)
df.show(truncate=False)

# Current Date
df.select(current_date().alias("current_date")).show(1)

# Date Formatting & Conversion
df.select(col("JoinDate"), date_format("JoinDate","MM-dd-yyyy").alias("date_format")).show()
df.select(col("JoinDate"), to_date("JoinDate","yyyy-MM-dd").alias("to_date")).show()

# Date Difference & Month Difference
df.select(col("JoinDate"), datediff(current_date(), "JoinDate").alias("datediff")).show()
df.select(col("JoinDate"), months_between(current_date(), "JoinDate").alias("months_between")).show()

# Truncate by Month/Year
df.select(col("JoinDate"), trunc("JoinDate","Month").alias("Month_Trunc"), trunc("JoinDate","Year").alias("Year_Trunc")).show()

# Add/Subtract Months and Days
df.select(col("JoinDate"),
          add_months("JoinDate",3).alias("Add3M"),
          add_months("JoinDate",-3).alias("Sub3M"),
          date_add("JoinDate",5).alias("Add5D"),
          date_sub("JoinDate",5).alias("Sub5D")).show()

# Extract Day Info
df.select("JoinDate",
          dayofweek("JoinDate").alias("DayOfWeek"),
          dayofmonth("JoinDate").alias("DayOfMonth"),
          dayofyear("JoinDate").alias("DayOfYear")).show()

# Current Timestamp
df.select(current_timestamp().alias("Current_Timestamp")).show(1, truncate=False)

# Calculate Age in Years
df_with_date = df.withColumn("date_col", to_date("JoinDate","yyyy-MM-dd"))
df_with_age = df_with_date.withColumn("AgeYears", (datediff(current_date(),col("date_col"))/365.25).cast("int"))
df_with_age.show()

# Average Age
df_with_age.agg(avg("AgeYears").alias("Average_Age")).show()

# Oldest and Youngest Employee
df_with_age.orderBy(col("AgeYears").asc()).limit(1).show()
df_with_age.orderBy(col("AgeYears").desc()).limit(1).show()

# Filter Employees Joined between Jan–May
df_with_age.withColumn("Month", month("date_col")).filter((col("Month")>=1)&(col("Month")<=5)).show()

# Extra Date-Time Functions
df.select("JoinDate", last_day("JoinDate").alias("Month_End")).show()
df.select("JoinDate", quarter("JoinDate").alias("Quarter")).show()
df.select("JoinDate", date_trunc("month","JoinDate").alias("Truncated_Month")).show()

# Unix Timestamp Conversion
df.select(from_unixtime(lit(1700000000),"yyyy-MM-dd HH:mm:ss").alias("FromUnix")).show()
df.select(unix_timestamp().alias("Unix_Timestamp")).show()
""")
    
def q7():
    print("""
# ===============================================
# EXPERIMENT 7 – PYSPARK WINDOW FUNCTIONS
# ===============================================

# Step 1: Import Libraries
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import *

# Step 2: Create Spark Session
spark = SparkSession.builder.appName("PySpark_WindowFunction_Example").getOrCreate()

# Step 3: Sample Student Data
simpleData = [
    ("Arun", "Maths", 85),
    ("Bala", "Maths", 92),
    ("Chitra", "Maths", 85),
    ("Deepak", "Science", 78),
    ("Elango", "Science", 88),
    ("Farhan", "Science", 91),
    ("Geeta", "English", 72),
    ("Hari", "English", 85),
    ("Indra", "English", 92),
    ("John", "English", 85)
]
columns = ["student_name", "subject", "marks"]
df = spark.createDataFrame(data=simpleData, schema=columns)

# Step 4: Display DataFrame
df.printSchema()
df.show(truncate=False)

# Step 5: Define Window Specifications
windowSpec = Window.partitionBy("subject").orderBy("marks")
windowSpecAgg = Window.partitionBy("subject")

# Step 6: Row Number & Ranking Functions
df.withColumn("row_number", row_number().over(windowSpec)).show()
df.withColumn("rank", rank().over(windowSpec)).show()
df.withColumn("dense_rank", dense_rank().over(windowSpec)).show()
df.withColumn("percent_rank", percent_rank().over(windowSpec)).show()
df.withColumn("ntile", ntile(2).over(windowSpec)).show()
df.withColumn("cume_dist", cume_dist().over(windowSpec)).show()

# Step 7: Lag & Lead Functions
df.withColumn("lag", lag("marks", 1).over(windowSpec)).show()
df.withColumn("lead", lead("marks", 1).over(windowSpec)).show()

# Step 8: Aggregate Functions over Window
df.withColumn("avg", avg("marks").over(windowSpecAgg)) \\
  .withColumn("sum", sum("marks").over(windowSpecAgg)) \\
  .withColumn("min", min("marks").over(windowSpecAgg)) \\
  .withColumn("max", max("marks").over(windowSpecAgg)) \\
  .show()

# Step 9: First & Last Values
df.withColumn("first_value", first("marks").over(windowSpec)).show()
df.withColumn("last_value", last("marks").over(windowSpec)).show()

# Step 10: Collect List & Collect Set
df.withColumn("all_marks_list", collect_list("marks").over(windowSpecAgg)).show()
df.withColumn("unique_marks", collect_set("marks").over(windowSpecAgg)).show()

# Step 11: Stop Spark Session
spark.stop()
""")
def q9():
    print("""
# ===============================================
# EXPERIMENT 9 – PYSPARK MACHINE LEARNING (IRIS CLASSIFICATION)
# ===============================================

# Step 1: Import Libraries
from pyspark.sql import SparkSession
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.classification import LogisticRegression, DecisionTreeClassifier, RandomForestClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

# Step 2: Create Spark Session
spark = SparkSession.builder.appName("IrisClassification").getOrCreate()

# Step 3: Load Data
data = spark.read.csv("/content/Iris.csv", header=True, inferSchema=True)

# Step 4: Convert Label to Numeric
indexer = StringIndexer(inputCol="Species", outputCol="label")
data = indexer.fit(data).transform(data)

# Step 5: Assemble Features
assembler = VectorAssembler(
    inputCols=["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"],
    outputCol="features"
)
data = assembler.transform(data)

# Step 6: Split Data
train, test = data.randomSplit([0.7, 0.3], seed=42)

# Step 7: Evaluator
evaluator = MulticlassClassificationEvaluator(
    labelCol="label", predictionCol="prediction", metricName="accuracy"
)

# Step 8: Logistic Regression
lr = LogisticRegression(featuresCol="features", labelCol="label")
lr_model = lr.fit(train)
lr_pred = lr_model.transform(test)
lr_pred.select("features", "label", "prediction").show(5)
lr_accuracy = evaluator.evaluate(lr_pred)
print("Logistic Regression Accuracy:", lr_accuracy)

# Step 9: Decision Tree
dt = DecisionTreeClassifier(featuresCol="features", labelCol="label")
dt_model = dt.fit(train)
dt_pred = dt_model.transform(test)
dt_pred.select("features", "label", "prediction").show(5)
dt_accuracy = evaluator.evaluate(dt_pred)
print("Decision Tree Accuracy:", dt_accuracy)

# Step 10: Random Forest
rf = RandomForestClassifier(featuresCol="features", labelCol="label", numTrees=10)
rf_model = rf.fit(train)
rf_pred = rf_model.transform(test)
rf_pred.select("features", "label", "prediction").show(5)
rf_accuracy = evaluator.evaluate(rf_pred)
print("Random Forest Accuracy:", rf_accuracy)

# Step 11: Stop Spark Session
spark.stop()
""")
def q10():
    print("""
# ===============================================
# EXPERIMENT 10 – PYSPARK CLUSTERING (KMeans, GMM, Bisecting KMeans)
# ===============================================

# Step 1: Import Libraries
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.clustering import KMeans, GaussianMixture, BisectingKMeans
from pyspark.ml.evaluation import ClusteringEvaluator
import matplotlib.pyplot as plt

# =============================
# 🔹 KMeans Clustering
# =============================
spark = SparkSession.builder.appName("KMeansMall").getOrCreate()

df = spark.read.csv("/content/Mall_Customers.csv", header=True, inferSchema=True)
data = df.select("Age", "Annual Income (k$)", "Spending Score (1-100)")

assembler = VectorAssembler(inputCols=["Age","Annual Income (k$)","Spending Score (1-100)"], outputCol="features")
dataset = assembler.transform(data).select("features")

kmeans = KMeans(k=5, seed=1, featuresCol="features", predictionCol="prediction")
kmeans_model = kmeans.fit(dataset)
kmeans_pred = kmeans_model.transform(dataset)

evaluator = ClusteringEvaluator()
silhouette = evaluator.evaluate(kmeans_pred)
print("KMeans Silhouette Score:", silhouette)
print("KMeans Cluster Centers:")
for center in kmeans_model.clusterCenters():
    print(center)

pdf = kmeans_pred.toPandas()
plt.scatter(pdf["features"].apply(lambda x:x[1]), pdf["features"].apply(lambda x:x[2]), c=pdf["prediction"], cmap="rainbow")
plt.xlabel("Annual Income (k$)")
plt.ylabel("Spending Score (1-100)")
plt.title("KMeans Clustering")
plt.show()

spark.stop()

# =============================
# 🔹 Gaussian Mixture Model (GMM) Clustering
# =============================
spark = SparkSession.builder.appName("GMM_Mall").getOrCreate()

df = spark.read.csv("/content/Mall_Customers.csv", header=True, inferSchema=True)
data = df.select("Age", "Annual Income (k$)", "Spending Score (1-100)")

assembler = VectorAssembler(inputCols=["Age","Annual Income (k$)","Spending Score (1-100)"], outputCol="features")
dataset = assembler.transform(data).select("features")

gmm = GaussianMixture(k=5, featuresCol="features", predictionCol="prediction")
gmm_model = gmm.fit(dataset)
gmm_pred = gmm_model.transform(dataset)

silhouette = evaluator.evaluate(gmm_pred)
print("GMM Silhouette Score:", silhouette)
print("GMM Gaussian Means:")
for row in gmm_model.gaussiansDF.collect():
    print(row["mean"].values)

pdf = gmm_pred.toPandas()
plt.scatter(pdf["features"].apply(lambda x:x[1]), pdf["features"].apply(lambda x:x[2]), c=pdf["prediction"], cmap="rainbow")
plt.xlabel("Annual Income (k$)")
plt.ylabel("Spending Score (1-100)")
plt.title("Gaussian Mixture Model Clustering")
plt.show()

spark.stop()

# =============================
# 🔹 Bisecting KMeans Clustering
# =============================
spark = SparkSession.builder.appName("BisectingKMeans_Mall").getOrCreate()

df = spark.read.csv("/content/Mall_Customers.csv", header=True, inferSchema=True)
data = df.select("Age", "Annual Income (k$)", "Spending Score (1-100)")

assembler = VectorAssembler(inputCols=["Age","Annual Income (k$)","Spending Score (1-100)"], outputCol="features")
dataset = assembler.transform(data).select("features")

bkmeans = BisectingKMeans(k=5, seed=1, featuresCol="features", predictionCol="prediction")
bkmeans_model = bkmeans.fit(dataset)
bkmeans_pred = bkmeans_model.transform(dataset)

silhouette = evaluator.evaluate(bkmeans_pred)
print("Bisecting KMeans Silhouette Score:", silhouette)
print("Bisecting KMeans Cluster Centers:")
for center in bkmeans_model.clusterCenters():
    print(center)

pdf = bkmeans_pred.toPandas()
plt.scatter(pdf["features"].apply(lambda x:x[1]), pdf["features"].apply(lambda x:x[2]), c=pdf["prediction"], cmap="rainbow")
plt.xlabel("Annual Income (k$)")
plt.ylabel("Spending Score (1-100)")
plt.title("Bisecting KMeans Clustering")
plt.show()

spark.stop()
""")
