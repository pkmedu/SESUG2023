1  #!/usr/bin/env python
2  # coding: utf-8
3  
4  # **step 1**
5  # - note the python libraries/modules
6  
7  # import libraries
8  import pandas as pd
9  import requests
10  from bs4 import BeautifulSoup
11  from urllib.parse import quote
12  
13  # **step 2**
14  # - get the list of numerical year options from the main page
15  # - save as list of tuples with year and url
16  
17  # main page response
18  main_page = requests.get("https://meps.ahrq.gov/data_stats/download_data_files.jsp")
19  main_soup = BeautifulSoup(main_page.text, "html.parser")
20  
21  # get list of data years and links for each year
22  # skip the "All years" (i.e. non-digit options)
23  base_year_url = "https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_results.jsp?cboDataYear="
24  year_url_suffix = "&buttonYearandDataType=Search"
25  
26  year_options = main_soup.select_one('select[name="cboDataYear"]').select("option")
27  
28  year_url_list = [
29      (x.get("value"), base_year_url + quote(x.get("value")) + year_url_suffix)
30      for x in year_options
31      if x.get("value").isdigit()
32  ]
33  
34  # **step 3**
35  # - use the year_url_list list of tuples to get "HC-" zip file links
36  # - save these in list of dictionaries
37  
38  base_hc_url = "https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_detail.jsp?cboPufNumber="
39  zip_link_list = []
40  for year, year_url in year_url_list:
41      try:
42          response = requests.get(year_url)
43          response.raise_for_status()
44          try:
45              dfs = pd.read_html(response.text)
46              hc_df = pd.DataFrame()
47              for df in dfs:
48                  if "File(s), Documentation & Codebooks" in df.columns:
49                      hc_df = pd.concat([hc_df, df], ignore_index=True)
50                      hc_df = hc_df.dropna(subset="PUF no.")
51                      hc_df = hc_df.loc[hc_df["PUF no."].str.contains("HC-")]
52                      hc_df = hc_df.drop_duplicates(subset="PUF no.")
53                      hc_df["hc_url"] = base_hc_url + hc_df["PUF no."]
54              if not hc_df.empty:
55                  hc_df.columns = [
56                      "puf_num",
57                      "Files",
58                      "Data_Update",
59                      "Year",
60                      "File_Type",
61                      "hc_url",
62                  ]
63                  for row in hc_df.itertuples():
64                      hc_response = requests.get(row.hc_url)
65                      hc_response.raise_for_status()
66                      hc_soup = BeautifulSoup(hc_response.text, features="lxml")
67                      try:
68                          meps_file = hc_soup.find(class_="OrangeBox").text
69                          for td in hc_soup.find_all("td"):
70                              zip_link_dict = {}
71                              if td.text.startswith("Data File"):
72                                  zip_link_dict["data_year"] = row.Year
73                                  zip_link_dict["puf_num"] = row.puf_num
74                                  zip_link_dict["meps_file"] = meps_file
75                                  zip_link_dict["file_format"] = td.text
76                                  zip_link_dict[
77                                      "zip_link"
78                                  ] = "https://meps.ahrq.gov" + td.find_next("a").get(
79                                      "href"
80                                  ).strip(
81                                      ".."
82                                  )
83                                  zip_link_list.append(zip_link_dict)
84                      except:
85                          # catch your exceptions here
86                          pass
87          except requests.exceptions.HTTPError as err:
88              print(err)
89      except requests.exceptions.HTTPError as httperr:
90          print(httperr)
91  
92  # **step 4**
93  # - save the list of dictionaries to pandas dataframe
94  # - deduplicate
95  # - clean up meps_file column to remove "PUF no." prefix
96  # - clean up file_format column to remove "Data File" prefix
97  # - sort the dataframe in certain order
98  # - get n rows of the dataframe
99  
100  meps_df = pd.DataFrame(zip_link_list)
101  meps_df.drop_duplicates(inplace=True)
102  meps_df["meps_file"] = meps_df["meps_file"].str.split(": ", n=1).str[-1]
103  meps_df["file_format"] = meps_df["file_format"].str.split(", ", n=1).str[-1]
104  meps_df = meps_df.sort_values(by=['data_year','puf_num', 'file_format'], ascending=[False, True, True])
105  print(meps_df.head(5))
106  
107  # **step 4 (continued)**
108  # - obtain the current date (timestamp)
109  # - save the dataframe as an excel file
110  
111  today = pd.Timestamp("now").strftime("%Y-%m-%d")
112  meps_df.to_excel(f"C:\SESUG_2023\Python_Solution_WS_{today}.xlsx", index=False)
113  
