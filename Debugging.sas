DM "Log; clear; output; clear; odsresults; clear";

/* URL elements */
    %let path = c:\SESUG_2023;
    %let pufnum = HC-060;
	%let base_url = https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_detail.jsp?cboPufNumber=;
	/* Combine the URL elements */
  	%let puf_url = &base_url.&pufnum.;

filename  pufresp "&path\PUF_LIST_%sysfunc(translate(&pufnum, '_', '-'))..txt";
		
	proc http
		url="&puf_url."
		out= pufresp;
	run;
			
	data puf_list_%sysfunc(translate(&pufnum, '_', '-')) /*(keep=puf_num file_format zip_link)*/;
		length puf_num $15 file_format $150 zip_link $200;
		infile pufresp length = reclen lrecl = 32767 end=eof;
			
		prx_data_file = prxparse('/<td width="50%" height="0" class="bottomRightgrayBorder">Data File.*, (.+)<\/td>/');
		prx_zip = prxparse('/<a href="\.\.\/(data_files(\/pufs)*\/.+\.zip)">ZIP<\/a>/');
   /************************************************************************************************************************************
        <td width="50%" class="sectionDividerGrey"><a href="../data_files/pufs/h60dat.zip">ZIP</a> <span class="xsmall">(14 MB)</span>                
		<td width="50%" class="sectionDividerGrey"><a href="../data_files/h60ssp.zip">ZIP</a> <span class="xsmall">(14 MB)</span> 
        <td width="50%" class="sectionDividerGrey"><a href="../data_files/pufs/h61dat.zip">ZIP</a> <span class="xsmall">(2.2 MB)</span> 
		<td width="50%" class="sectionDividerGrey"><a href="../data_files/pufs/h61ssp.zip">ZIP</a> <span class="xsmall">(3.0 MB)</span> 
                          
   ********************************************************************************************************************************/	
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
    options nocenter ls=132;
    proc print;
	var puf_num file_format zip_link;
	run;

	proc print;
	var prx_data_file: start end;
	run;

	proc print;
	var prx_zip: start end;
	run;
