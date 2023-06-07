

%let Path = C:\SESUG_2023;
options validvarname=any;
Libname XL XLSX "&Path\SAS_MEPS_zip_links_2023-06-07.xlsx";
Libname new "&Path";
data new.SAS_Output;
  set XL.sheet1;
run;
libname XL CLEAR; 


%let xPath = C:\Python\Web_scraping\output;
options validvarname=any;
Libname XL XLSX "&xPath\MEPS_zip_links_2023-06-06.xlsx";
Libname new "&Path";
data new.Python_Output;
  set XL.sheet1;
run;
libname XL CLEAR; 


proc sort data=new.sas_output out=sas_output nodupkey;
by _ALL_;
run;

proc sort data=new.python_output out=python_output nodupkey;
by _ALL_;
run;

data both not_both;
merge sas_output (in=a) python_output (in=b); by _ALL_;
if a=b then output both;
else if b=1 and a ne 1 then output not_both;
run;

