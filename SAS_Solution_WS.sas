%let path = c:\SESUG_2023;
/* Step 1: Fetch the main MEPS-HC web page's contents using PROC HTTP */
filename source temp;
proc http
     url = "https://meps.ahrq.gov/data_stats/download_data_files.jsp"
     out=source;
run;

/* Step 2:  Parse the MEPS-HC main web page */
/* Get years from dropdown options list */
options generic;
data year_values;
    length year 8;
    infile source dlm='<' expandtabs truncover;
    input @'<option value="'   @'>' year ??;
if not missing (year);
run;

filename source clear;

/* Step 3: Call Proc HTTP for each year_url */
%macro get_year(year);
	filename yearresp "&path\hc_response.txt";
	%local base_url data_year_param search_param year_url;
	/* URL elements */
	%let base_url = https://meps.ahrq.gov/data_stats/download_data_files_results.jsp?;
  	%let data_year_param = cboDataYear=&year.;
  	%let search_param = %nrstr(&buttonYearandDataType=Search);
	
	/* Combine the URL elements to construct the year url*/
  	%let year_url = &base_url.&data_year_param.&search_param.;
	
	/* Call PROC HTTP to retrieve the content */
	/* of each year search results */
  	proc http
  		url = "&year_url."
    	out=yearresp;
  	run;

	data year_list_&year. (keep=puf_num meps_file data_year);
	  	length puf_num $15 meps_file $150 data_year $10;
		infile yearresp length = reclen lrecl = 32767 end=eof;

		/* regex to get the PUF num in the table of results */
		retain prx_puf;
		prx_puf = prxparse('/<a href="download_data_files_detail\.jsp\?cboPufNumber=.+\">(.+)<\/a>/');

		/* regex to get the meps file */
		retain prx_meps;
	  	prx_meps = prxparse('/<td height="30" align="left" valign="top" class="bottomRightgrayBorder"><div align="left" class="contentStyle">(.+)<\/font>/');

		/* regex for data year */
		retain prx_data_year;
	  	prx_data_year = prxparse('/<td width="1" height="30" align="left" valign="top" class="bottomRightgrayBorder"><div align="left" class="contentStyle">(.+)<\/font><\/div><\/td>/');

		/* Read the HTML line by line */
		do while (not eof);
			input html_line $varying32767. reclen;	    
		   	if prxmatch(prx_puf, html_line) > 0 then do;
		   		call prxposn(prx_puf, 1, start, end);
	      		puf_num = substr(html_line, start, end);
		   	end;
		    if prxmatch(prx_meps, html_line) > 0 then do;
	       		call prxposn(prx_meps, 1, start, end);
	      		meps_file = substr(html_line, start, end);
	      		meps_file = prxchange('s/<.+>//', -1, meps_file);	/* remove any stray html tags */
		    end;
		    if prxmatch(prx_data_year, html_line) > 0 then do;
		   		call prxposn(prx_data_year, 1, start, end);
	      		data_year = substr(html_line, start, end);
	      		output year_list_&year.;
		   	end;
		end;
	run;

	filename yearresp clear;
	
%mend get_year;

/* Loop through each year of the year_values dataset and call the macro */
data _null_;
	set year_values;
    call execute('%nrstr(%get_year('||strip(year)||'));');
run;

/* Concatenate all year_list_YEAR datasets */
/* Just keep obs with puf_num beginning HC- */
data year_list;
	set year_list_: ;
	where substr(puf_num, 1, 2) = 'HC';
run;	

/* De-dup */
proc sort data=year_list nodupkey;	
  by _ALL_;
run;

/* Step 4: Get the zip files for each HC- puf_num. */
%macro get_puf(pufnum);
    %local base_url puf_url;
	filename pufresp temp;

	/* URL elements */
	%let base_url = https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_detail.jsp?cboPufNumber=;
	
	/* Combine the URL elements to construct the PUF url */
  	%let puf_url = &base_url.&pufnum.;
		
	proc http
		url="&puf_url."
		out= pufresp;
	run;
			
	data puf_list_%sysfunc(translate(&pufnum, '_', '-')) (keep=puf_num file_format zip_link);
		length puf_num $15 file_format $150 zip_link $200;
		infile pufresp length = reclen lrecl = 32767 end=eof;
		
        /* regex for the data file name */	
		retain prx_data_file;
        if _n_= 1 then prx_data_file = prxparse('/<td width="50%" height="0" class="bottomRightgrayBorder">Data File.*, (.+)<\/td>/');
        
		/* regex for the zip file download link */
		retain prx_zip;
        if _n_= 1 then prx_zip = prxparse('/<a href="\.\.\/(data_files[\/pufs]*\/.+\.zip)">ZIP<\/a>/');
        		
		do while (not eof);
			input html_line $varying32767. reclen;
			puf_num = "&pufnum.";
			if prxmatch(prx_data_file, html_line) > 0 then do;
				call prxposn(prx_data_file, 1, start, end);
		      	file_format = substr(html_line, start, end);
			end;
			
			if prxmatch(prx_zip, html_line) > 0 then do;
				call prxposn(prx_zip, 1, start, end);
		      	zip_link = cats("https://meps.ahrq.gov/", substr(html_line, start, end));
		      	output puf_list_%sysfunc(translate(&pufnum, '_', '-'));
			end;
		end;
	   
	run;

	filename pufresp clear;

%mend get_puf;

/* Loop through each puf_num of the year_list dataset and call the macro */
data _null_;
	set year_list;
	call execute('%nrstr(%get_puf('||strip(puf_num)||'));');
run;

/* Concatenate all puf_list datasets */
data puf_list;
	set puf_list_: ;
run;	

/* De-dup */
proc sort data=puf_list nodupkey;
	by _ALL_;
run;

/* Step 5: Merge year_list and puf_list */
proc sql;
	create table meps_zip_links as
	select y.puf_num, y.meps_file, y.data_year, p.file_format, p.zip_link
	from year_list as y,
		 puf_list as p
	where y.puf_num = p.puf_num
    order by data_year desc, puf_num, file_format;
quit;

/* Format the current date as "YYYY-MM-DD" */
%let current_date = %sysfunc(today());
%let formatted_date = %sysfunc(putn(&current_date., yymmdd10.));

/* Step 6: Direct proc report output to excel */
ods listing close;
ods excel file = "&path\SAS_Solution_WS_&formatted_date..xlsx" 
   options (sheet_name = 'Sheet1'
   flow="header,data" row_heights = '15'
   absolute_column_width='11,11,70,30,55'); 
proc report data=meps_zip_links; 
  column data_year puf_num meps_file file_format  zip_link;
  define puf_num / display ;
  define meps_file / display;
  define data_year / display;
  define file_format / display;
  define zip_link / display ;
  compute zip_link ;
    call define(_col_,"url",zip_link);
  endcomp;
run;
ods excel close;
ods listing;

