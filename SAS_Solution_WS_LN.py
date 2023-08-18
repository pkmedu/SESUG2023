1  %let path = c:\SESUG_2023;
2  /* Step 1: Fetch the main MEPS-HC web page's contents using PROC HTTP */
3  filename source temp;
4  proc http
5       url = "https://meps.ahrq.gov/data_stats/download_data_files.jsp"
6       out=source;
7  run;
8  
9  /* Step 2:  Parse the MEPS-HC main web page */
10  /* Get years from dropdown options list */
11  options generic;
12  data year_values;
13      length year 8;
14      infile source dlm='<' expandtabs truncover;
15      input @'<option value="'   @'>' year ??;
16  if not missing (year);
17  run;
18  
19  filename source clear;
20  
21  /* Step 3: Call Proc HTTP for each year_url */
22  %macro get_year(year);
23  	filename yearresp "&path\hc_response.txt";
24  	%local base_url data_year_param search_param year_url;
25  	/* URL elements */
26  	%let base_url = https://meps.ahrq.gov/data_stats/download_data_files_results.jsp?;
27    	%let data_year_param = cboDataYear=&year.;
28    	%let search_param = %nrstr(&buttonYearandDataType=Search);
29  	
30  	/* Combine the URL elements to construct the year url*/
31    	%let year_url = &base_url.&data_year_param.&search_param.;
32  	
33  	/* Call PROC HTTP to retrieve the content */
34  	/* of each year search results */
35    	proc http
36    		url = "&year_url."
37      	out=yearresp;
38    	run;
39  
40  	data year_list_&year. (keep=puf_num meps_file data_year);
41  	  	length puf_num $15 meps_file $150 data_year $10;
42  		infile yearresp length = reclen lrecl = 32767 end=eof;
43  
44  		/* regex to get the PUF num in the table of results */
45  		retain prx_puf;
46          if _n_= 1 then prx_puf = prxparse('/<a href="download_data_files_detail\.jsp\?cboPufNumber=.+\">(.+)<\/a>/');
47  
48  		/* regex to get the meps file */
49          retain prx_meps;
50          if _n_=1 then prx_meps = prxparse('/<td height="30" align="left" valign="top" class="bottomRightgrayBorder"><div align="left" class="contentStyle">(.+)<\/font>/');
51  
52  		/* regex for data year */
53  		retain prx_data_year;
54          if _n_= 1 then prx_data_year = prxparse('/<td width="1" height="30" align="left" valign="top" class="bottomRightgrayBorder"><div align="left" class="contentStyle">(.+)<\/font><\/div><\/td>/');
55  
56  		/* Read the HTML line by line */
57  		do while (not eof);
58  			input html_line $varying32767. reclen;	    
59  		   	if prxmatch(prx_puf, html_line) > 0 then do;
60  		   		call prxposn(prx_puf, 1, start, end);
61  	      		puf_num = substr(html_line, start, end);
62  		   	end;
63  		    if prxmatch(prx_meps, html_line) > 0 then do;
64  	       		call prxposn(prx_meps, 1, start, end);
65  	      		meps_file = substr(html_line, start, end);
66  	      		meps_file = prxchange('s/<.+>//', -1, meps_file);	/* remove any stray html tags */
67  		    end;
68  		    if prxmatch(prx_data_year, html_line) > 0 then do;
69  		   		call prxposn(prx_data_year, 1, start, end);
70  	      		data_year = substr(html_line, start, end);
71  	      		output year_list_&year.;
72  		   	end;
73  		end;
74  	run;
75  
76  	filename yearresp clear;
77  	
78  %mend get_year;
79  
80  /* Loop through each year of the year_values dataset and call the macro */
81  data _null_;
82  	set year_values;
83      call execute('%nrstr(%get_year('||strip(year)||'));');
84  run;
85  
86  /* Concatenate all year_list_YEAR datasets */
87  /* Just keep obs with puf_num beginning HC- */
88  data year_list;
89  	set year_list_: ;
90  	where substr(puf_num, 1, 2) = 'HC';
91  run;	
92  
93  /* De-dup */
94  proc sort data=year_list nodupkey;	
95    by _ALL_;
96  run;
97  
98  /* Step 4: Get the zip files for each HC- puf_num. */
99  %macro get_puf(pufnum);
100      %local base_url puf_url;
101  	filename pufresp temp;
102  
103  	/* URL elements */
104  	%let base_url = https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_detail.jsp?cboPufNumber=;
105  	
106  	/* Combine the URL elements to construct the PUF url */
107    	%let puf_url = &base_url.&pufnum.;
108  		
109  	proc http
110  		url="&puf_url."
111  		out= pufresp;
112  	run;
113  			
114  	data puf_list_%sysfunc(translate(&pufnum, '_', '-')) (keep=puf_num file_format zip_link);
115  		length puf_num $15 file_format $150 zip_link $200;
116  		infile pufresp length = reclen lrecl = 32767 end=eof;
117  		
118          /* regex for the data file name */	
119  		retain prx_data_file;
120          if _n_= 1 then prx_data_file = prxparse('/<td width="50%" height="0" class="bottomRightgrayBorder">Data File.*, (.+)<\/td>/');
121          
122  		/* regex for the zip file download link */
123  		retain prx_zip;
124          if _n_= 1 then prx_zip = prxparse('/<a href="\.\.\/(data_files[\/pufs]*\/.+\.zip)">ZIP<\/a>/');
125          		
126  		do while (not eof);
127  			input html_line $varying32767. reclen;
128  			puf_num = "&pufnum.";
129  			if prxmatch(prx_data_file, html_line) > 0 then do;
130  				call prxposn(prx_data_file, 1, start, end);
131  		      	file_format = substr(html_line, start, end);
132  			end;
133  			
134  			if prxmatch(prx_zip, html_line) > 0 then do;
135  				call prxposn(prx_zip, 1, start, end);
136  		      	zip_link = cats("https://meps.ahrq.gov/", substr(html_line, start, end));
137  		      	output puf_list_%sysfunc(translate(&pufnum, '_', '-'));
138  			end;
139  		end;
140  	   
141  	run;
142  
143  	filename pufresp clear;
144  
145  %mend get_puf;
146  
147  /* Loop through each puf_num of the year_list dataset and call the macro */
148  data _null_;
149  	set year_list;
150  	call execute('%nrstr(%get_puf('||strip(puf_num)||'));');
151  run;
152  
153  /* Concatenate all puf_list datasets */
154  data puf_list;
155  	set puf_list_: ;
156  run;	
157  
158  /* De-dup */
159  proc sort data=puf_list nodupkey;
160  	by _ALL_;
161  run;
162  
163  /* Step 5: Merge year_list and puf_list */
164  proc sql;
165  	create table meps_zip_links as
166  	select y.puf_num, y.meps_file, y.data_year, p.file_format, p.zip_link
167  	from year_list as y,
168  		 puf_list as p
169  	where y.puf_num = p.puf_num
170      order by data_year desc, puf_num, file_format;
171  quit;
172  
173  /* Format the current date as "YYYY-MM-DD" */
174  %let current_date = %sysfunc(today());
175  %let formatted_date = %sysfunc(putn(&current_date., yymmdd10.));
176  
177  /* Step 6: Direct proc report output to excel */
178  ods listing close;
179  ods excel file = "&path\SAS_Solution_WS_&formatted_date..xlsx" 
180     options (sheet_name = 'Sheet1'
181     flow="header,data" row_heights = '15'
182     absolute_column_width='11,11,70,30,55'); 
183  proc report data=meps_zip_links; 
184    column data_year puf_num meps_file file_format  zip_link;
185    define puf_num / display ;
186    define meps_file / display;
187    define data_year / display;
188    define file_format / display;
189    define zip_link / display ;
190    compute zip_link ;
191      call define(_col_,"url",zip_link);
192    endcomp;
193  run;
194  ods excel close;
195  ods listing;
196  
