import os
import pandas as pd
from access_parser import AccessParser

# working through logic with a single file
# start with the most basic tables we need like HD per year
# db_filepath = "/Users/tereuter/Desktop/ipeds_databases/IPEDS201617.accdb" # fails, corrupt file?
db_filepath = "/Users/tereuter/Desktop/ipeds_databases/IPEDS202223.accdb"
db = AccessParser(db_filepath)

# display table catalog
print("Tables in the database:")
for table_name in db.catalog.keys():
    print(table_name)

# # parse a specific table
# table_name = "HD2004"
# parsed_table_data = db.parse_table(table_name)

# # convert to df
# df = pd.DataFrame(parsed_table_data)

# # print result
# print(df.head())

# # 
# import access_parser
# import pandas as pd

# accdb_file = '/Users/tereuter/Desktop/ipeds_databases/IPEDS202223.accdb'
# try:
#     db = access_parser.AccessParser(accdb_file)
#     for table_name in db.tables():
#         print(f"Exporting table '{table_name}'...")
#         table_data = db.fetch_table(table_name)
#         df = pd.DataFrame(table_data['data'], columns=table_data['columns'])
#         # output_file = f"{table_name}.csv"
#         # df.to_csv(output_file, index=False)
#         # print(f"Saved {output_file}")
# except Exception as e:
#     print(f"Error parsing ACCDB file: {e}")