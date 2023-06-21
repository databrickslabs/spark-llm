from langchain import FewShotPromptTemplate
from langchain.prompts.prompt import PromptTemplate

SEARCH_TEMPLATE = """Given a Query and a list of Google Search Results, return the link
from a reputable website which contains the data set to answer the question. {columns}
Query:{query}
Google Search Results: 
```
{search_results}
```
The answer MUST contain the url link only
"""

SEARCH_PROMPT = PromptTemplate(
    input_variables=["query", "search_results", "columns"], template=SEARCH_TEMPLATE
)

SQL_TEMPLATE = """Given the following question:
```
{query}
```
I got the following answer from a web page:
```
{web_content}
```
Now help me write a SQL query to store the answer into a temp view.
Here is an example of how to store data into a temp view:
```
CREATE OR REPLACE TEMP VIEW movies AS SELECT * FROM VALUES('Citizen Kane', 1941), ('Schindler\'s List', 1993) AS v1(title, year)
```
{columns}
The answer MUST contain query only.
"""

SQL_PROMPT = PromptTemplate(
    input_variables=["query", "web_content", "columns"], template=SQL_TEMPLATE
)

TRANSFORM_TEMPLATE = """
Given a Spark temp view `{view_name}` with the following columns:
```
{columns}
```
Write a Spark SQL query to retrieve: {desc}
The answer MUST contain query only.
"""

TRANSFORM_PROMPT = PromptTemplate(
    input_variables=["view_name", "columns", "desc"], template=TRANSFORM_TEMPLATE
)

EXPLAIN_PREFIX = """You are an Apache Spark SQL expert, who can summary what a dataframe retrieves. Given an analyzed 
query plan of a dataframe, you will 
1. convert the dataframe to SQL query. Note that an explain output contains plan 
nodes separated by `\\n`. Each plan node has its own expressions and expression ids. 
2. summary what the sql query retrieves. 
"""

EXPLAIN_SUFFIX = "analyzed_plan: {input}\nexplain:"

_plan1 = """
GlobalLimit 100
    +- LocalLimit 100
       +- Sort [d_year ASC NULLS FIRST, sum_agg DESC NULLS LAST, brand_id ASC NULLS FIRST], true
          +- Aggregate [d_year, i_brand, i_brand_id], [d_year, i_brand_id AS brand_id, i_brand AS brand, sum(ss_ext_sales_price) AS sum_agg]
             +- Filter (((d_date_sk = ss_sold_date_sk) AND (ss_item_sk = i_item_sk)) AND ((i_manufact_id = 128) AND (d_moy = 11)))
                +- Join Inner
                   :- Join Inner
                   :  :- SubqueryAlias dt
                   :  :  +- SubqueryAlias spark_catalog.tpcds_sf1_delta.date_dim
                   :  :     +- Relation spark_catalog.tpcds_sf1_delta.date_dim[d_date_sk,d_date_id,d_date,d_month_seq,d_week_seq,d_quarter_seq,d_year,d_dow,d_moy,d_dom,d_qoy,d_fy_year,d_fy_quarter_seq,d_fy_week_seq,d_day_name,d_quarter_name,d_holiday,d_weekend,d_following_holiday,d_first_dom,d_last_dom,d_same_day_ly,d_same_day_lq,d_current_day,... 4 more fields] parquet
                   :  +- SubqueryAlias spark_catalog.tpcds_sf1_delta.store_sales
                   :     +- Relation spark_catalog.tpcds_sf1_delta.store_sales[ss_sold_date_sk,ss_sold_time_sk,ss_item_sk,ss_customer_sk,ss_cdemo_sk,ss_hdemo_sk,ss_addr_sk,ss_store_sk,ss_promo_sk,ss_ticket_numberL,ss_quantity,ss_wholesale_cost,ss_list_price,ss_sales_price,ss_ext_discount_amt,ss_ext_sales_price,ss_ext_wholesale_cost,ss_ext_list_price,ss_ext_tax,ss_coupon_amt,ss_net_paid,ss_net_paid_inc_tax,ss_net_profit] parquet
                   +- SubqueryAlias spark_catalog.tpcds_sf1_delta.item
                      +- Relation spark_catalog.tpcds_sf1_delta.item[i_item_sk,i_item_id,i_rec_start_date,i_rec_end_date,i_item_desc,i_current_price,i_wholesale_cost,i_brand_id,i_brand,i_class_id,i_class,i_category_id,i_category,i_manufact_id,i_manufact,i_size,i_formulation,i_color,i_units,i_container,i_manager_id,i_product_name] parquet
"""

_explain1 = """
The analyzed plan can be translated into the following SQL query:
```sql
SELECT
  dt.d_year,
  item.i_brand_id brand_id,
  item.i_brand brand,
  SUM(ss_ext_sales_price) sum_agg
FROM date_dim dt, store_sales, item
WHERE dt.d_date_sk = store_sales.ss_sold_date_sk
  AND store_sales.ss_item_sk = item.i_item_sk
  AND item.i_manufact_id = 128
  AND dt.d_moy = 11
GROUP BY dt.d_year, item.i_brand, item.i_brand_id
ORDER BY dt.d_year, sum_agg DESC, brand_id
LIMIT 100
```
In summary, this dataframe is retrieving the top 100 brands (specifically of items manufactured by manufacturer with id 128) with the highest total sales price for each year in the month of November. It presents the results sorted by year, total sales (in descending order), and brand id.
"""

_explain_examples = [{"analyzed_plan": _plan1, "explain": _explain1}]

_example_formatter = """
analyzed_plan: {analyzed_plan}
explain: {explain}
"""

_example_prompt = PromptTemplate(
    input_variables=["analyzed_plan", "explain"], template=_example_formatter
)

EXPLAIN_DF_PROMPT = FewShotPromptTemplate(
    examples=_explain_examples,
    example_prompt=_example_prompt,
    prefix=EXPLAIN_PREFIX,
    suffix=EXPLAIN_SUFFIX,
    input_variables=["input"],
    example_separator="\n\n",
)

PLOT_PROMPT_TEMPLATE = """
Given a pyspark dataframe `df`.
The output columns of `df`:
{columns}

{explain}

Now help me write python code to visualize the result of `df` using plotly:
1. Your code output should NOT include method 'append'.
2. Your could should NOT install any package with pip. 
3. Show the plot directly, instead of saving into a HTML.
{instruction}
"""

PLOT_PROMPT = PromptTemplate(
    input_variables=["columns", "explain", "instruction"], template=PLOT_PROMPT_TEMPLATE
)

VERIFY_TEMPLATE = """
Given a description of expected properties of a Spark temp view `{view_name}`
generate a Spark SQL query to retrieve ALL values that fail the expectation.
You should ONLY output the SQL query code (no explanation words).

For example:
Input:
desc = "expect no null column x"

Output:
select * from `{view_name}` where x is null

Input:
desc = "expect no A letter_grade"

Output:
select * from `{view_name}` where letter_grade = 'A'

Here is your input description: {desc}
"""

VERIFY_PROMPT = PromptTemplate(input_variables=["view_name", "desc"], template=VERIFY_TEMPLATE)

UDF_PREFIX = """
This is the documentation for a PySpark user-defined function (udf): pyspark.sql.functions.udf

A udf creates a deterministic, reusable function in Spark. It can take any data type as a parameter, 
and by default returns a String (although it can return any data type). 
The point is to reuse a function on several dataframes and SQL functions.

Given 1) input arguments, 2) a description of the udf functionality,
3) the udf return type, and 4) the udf function name, 
generate and return a callable udf.
        
Return ONLY the callable resulting udf function (no explanation words). 
Include any necessary import statements INSIDE the function definition.
For example:
def gen_random():
    import random
    return random.randint(0, 10)
"""

UDF_SUFFIX = """
input_args_types: {input_args_types}
input_desc: {desc}
return_type: {return_type}
udf_name: {udf_name}
output:\n
"""

_udf_output1 = """
def to_upper(s) -> str:
    if s is not None:
        return s.upper()
"""

_udf_output2 = """
def add_one(x) -> int:
    if x is not None:
        return x + 1
"""

_udf_examples = [{"input_args_types": "(s: str)",
                  "desc": "Convert string s to uppercase",
                  "return_type": "str",
                  "udf_name": "to_upper",
                  "output": _udf_output1},
                {"input_args_types": "(x: int)",
                  "desc": "Add 1",
                  "return_type": "int",
                  "udf_name": "add_one",
                  "output": _udf_output2}]

_udf_formatter = """
input_args_types: {input_args_types}
desc: {desc}
return_type: {return_type}
udf_name: {udf_name}
output: {output}
"""

_udf_prompt = PromptTemplate(
    input_variables=["input_args_types", "desc", "return_type", "udf_name", "output"], template=_udf_formatter
)

UDF_PROMPT = FewShotPromptTemplate(
    examples=_udf_examples,
    example_prompt=_udf_prompt,
    prefix=UDF_PREFIX,
    suffix=UDF_SUFFIX,
    input_variables=["input_args_types", "desc", "return_type", "udf_name"],
    example_separator="\n\n",
)

