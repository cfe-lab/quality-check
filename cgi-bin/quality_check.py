#!/Library/Frameworks/Python.framework/Versions/3.6/bin/python3

import os

import sys  # Add the path to openpyxl (excel files). (And other web dependencies.)
import re
import cgi
import smtplib
from email.mime.text import MIMEText

#sys.path.append("/Users/B_Team_iMac/Sites/cgi-bin/python_dependencies/libraries/")
sys.path.append( "{}/../python_dependencies/libraries/".format(os.getcwd()) )
from openpyxl import Workbook
import openpyxl
from openpyxl.styles import colors
from openpyxl.styles import Font, Color

#sys.path.append("/Users/B_Team_iMac/Sites/cgi-bin/python_dependencies/3.6/util_scripts/")
sys.path.append( "{}/../python_dependencies/3.6/util_scripts/".format(os.getcwd()) )
import sequence_utils
import format_utils
import mailer
import web_output


##### Create and instance of the site class for website creation.	


website = web_output.Site("Results", False)


##### Get website input.


form = cgi.FieldStorage()  # Get form data from the website.

file_item = form['file']  # Get the file item

# Check if the file was submitted to the form.
if file_item.filename:
	# Read the file's text.
	input_field_text = [e+'\n' for e in str( file_item.value.decode("utf-8") ).replace('\r', '\n').split('\n') if e]

else:
	# Get user input string and convert it into a list of lines.
	input_field_text = [e+'\n' for e in str( form.getvalue("fastaInputArea") ).replace('\r', '\n').split('\n') if e]

email_address_string = str(form.getvalue("emailAddress"))  # Get the email address value.

# Add the parameters to a list.
flag_list = []  
flag_list.append( 0 if form.getvalue("div3") == None else 1 )
flag_list.append( 0 if form.getvalue("start") == None else 1 )
flag_list.append( 0 if form.getvalue("stop") == None else 1 )
flag_list.append( 0 if form.getvalue("internal") == None else 1 )
flag_list.append( 0 if form.getvalue("mixture") == None else 1 )

#website.send( input_field_text )

# Convert file to a list of tuples.
fasta_list = sequence_utils.convert_fasta( input_field_text )

# Convert the dna sequences to uppercase.
index = 0
for tuple in fasta_list:
	fasta_list[index] = (tuple[0], tuple[1].upper())
	index += 1


##### Run tests on the given sequences and save the results in matrix. 


results_matrix = []  # This list of dictionaries (matrix?) will hold the results for all the sequences.

# Loop through each sequence and run the tests on it.
for tuple in fasta_list:
	# Sequence properties.
	dna_sequence = tuple[1]

	output_dict = { "id" : tuple[0], "seq" : tuple[1]  }  # The output_list is initalized with the name of the sequence and the sequence.		
		
	##### Search for invalid characters.

	# Get a report that contains validity and bad characters.
	report = sequence_utils.invalid_in_sequence(dna_sequence)
	output_dict['isvalid'] = report[0]

	# If sequence in invalid give the user some info.
	if output_dict['isvalid'] == False:
		msg_first = "Found invalid characters in the sequence <em>{}</em>.  These characters may affect certain calculations.".format( tuple[0] )

		test_skipped = "None" * (1 if flag_list[1] + flag_list[2] + flag_list[3] == 0 else 0)
		msg_second = 'Could not run the following tests: <r style="color: red;">{}{}</r>'.format( test_skipped, ("Starts with M, "*flag_list[1]+"Stops with *, "*flag_list[2]+"Internal *, "*flag_list[3])[:-2]+'.' )
		
		invalid_char_string = ""
		for item in list(report[1:]):
			invalid_char_string += '<b style="color: green;">{}</b> at position {}, '.format(item[0], item[1])
		invalid_char_string = invalid_char_string[:-2] + '.'

		msg_third = "The following invalid characters were found: {}".format( invalid_char_string )

		website.send (msg_first + '<br>' + msg_second + '<br>' + msg_third + '<br><br>' )

	##### Run the div3 test.
	if flag_list[0] == 1:
		output_dict["div3"] = sequence_utils.seq_div3_test(dna_sequence)
	
	##### Run the start test.
	if flag_list[1] == 1 and output_dict['isvalid'] == True:
		output_dict["start"] = sequence_utils.seq_start_test(dna_sequence)
	
	##### Run the stop test.
	if flag_list[2] == 1 and output_dict['isvalid'] == True:
		output_dict["stop"] = sequence_utils.seq_stop_test(dna_sequence)
	
	##### Run the internal test.
	if flag_list[3] == 1 and output_dict['isvalid'] == True:
		output_dict["internal"] = sequence_utils.seq_internal_test(dna_sequence)
	
	##### Run the mixture test.
	mixture_results = sequence_utils.seq_mixture_test(dna_sequence)

	# Save the mixture percent composition even when checkbox is unchecked.
	output_dict["mixture_percent"] = mixture_results[1]	
	
	# Only the mixture dict is given when the checkbox is checked.
	if flag_list[4] == 1:
		output_dict["mixture"] = mixture_results[:1] + mixture_results[2:] 
	
	results_matrix.append(output_dict)  # Add the results for the current sequence to the main results (the matrix).


##### Output the immediate results to the webpage.


# Print the quick results title.
website.send ( '<br><h4 style="margin: 0;">Quick Results:</h4><br>' )
website.new_box()
website.send ( '<br>' )


# This function returns a string with the quick results for each parameter. 
def _quick_results_string(param_key, param_msg, matrix):
	counter = 0
	id_list_string = ""
	for seq_results_dict in matrix:  # Iterate through all dictionaries in the matrix.
		if param_key in seq_results_dict:  # Case: The current key IS in the dict.
			if seq_results_dict[param_key][0] == False:
				counter += 1
				id_list_string += seq_results_dict['id'] + ", "
				
	return "{} {}{}</b><br><br>".format("The following <b>{}</b> sequence(s)".format(counter) if counter != 0 else "No sequences", param_msg, (": <b>" + id_list_string[:-2] + '.') if counter != 0 else '.<b>')
	
# Output results for each section.
if flag_list[0] == 1:	
	website.send ( _quick_results_string('div3', "have lengths that are not divisible by 3", results_matrix) )

if flag_list[1] == 1:
	website.send ( _quick_results_string('start', "have an improper start codon", results_matrix) )

if flag_list[2] == 1:
	website.send ( _quick_results_string('stop', "have an improper end codon", results_matrix) )

if flag_list[3] == 1:
	website.send ( _quick_results_string('internal', "have internal end codons", results_matrix) )
	
if flag_list[4] == 1:
	website.send ( _quick_results_string('mixture', "contain mixtures", results_matrix) )


##### Create an xlsx file.


XLSX_FILENAME = "quality_check_data"

wb = Workbook()  # Create a new workbook.
ws = wb.active  # Create a new page. (worksheet [ws])
ws.title = "Data"  # Page title

# Create the title row information.
first_three_tests = ([] if flag_list[0] == 0 else ["Divisible by 3"]) + ([] if flag_list[1] == 0 else ["Has Start Codon"]) + ([] if flag_list[2] == 0 else ["Has End Codon"]) 
tests = first_three_tests + ([] if flag_list[3] == 0 else ["No Internal Codons"]) + ([] if flag_list[4] == 0 else ["Contains No Mixtures"])
ws.append( ["Sequence ID", "Sequence", "Sequence Length"] + tests + ["% Mixtures"] )

# Create data row information.
for dict in results_matrix:
	sequence_id = dict['id']
	dna_sequence = dict['seq']
	sequence_length = len(dna_sequence)
	
	# Each of these are lists of length 1.
	div3     = [] if flag_list[0] == 0 else [ ("PASS" if dict['div3'][0] == True else "FAIL") ]
	start    = ([] if dict['isvalid'] else ["N/A (invalid character)"]) if flag_list[1] == 0 or dict['isvalid'] == False else [ ("PASS" if dict['start'][0] == True else "FAIL") ] 
	stop     = ([] if dict['isvalid'] else ["N/A (invalid character)"]) if flag_list[2] == 0 or dict['isvalid'] == False else [ ("PASS" if dict['stop'][0] == True else "FAIL") ]
	internal = ([] if dict['isvalid'] else ["N/A (invalid character)"]) if flag_list[3] == 0 or dict['isvalid'] == False else [ ("PASS" if dict['internal'][0] == True else "FAIL at {}".format(format_utils.format_list( dict['internal'][1:] ))) ]
	mixture  = [] if flag_list[4] == 0 else [ ("PASS" if dict['mixture'][0] == True else "FAIL.  Mixtures: {}".format(format_utils.format_list( [key for key in dict['mixture'][1].keys() if dict['mixture'][1][key] > 0] ))) ]
	
	percent_mixture = [ str(dict['mixture_percent']) + " %" ]
	
	ws.append( [sequence_id, dna_sequence, sequence_length] + div3 + start + stop + internal + mixture + percent_mixture )

# Add colour to fails.
for row in ws.iter_rows():
	for cell in row:
		if str(cell.value)[:4] == "FAIL" and cell.column != 'A':
			cell.font = Font(color=colors.RED)

# Save a string version of the excel workbook and send it to the file builder.
file_text = openpyxl.writer.excel.save_virtual_workbook(wb)
xlsx_file = mailer.create_file( XLSX_FILENAME, 'xlsx', file_text )


##### Send an email with the xlsx file in it.


website.new_box()
website.send ( '<br>' )

# Determine if an email should be sent.
if flag_list[0] + flag_list[1] + flag_list[2] + flag_list[3] + flag_list[4] == 0:
	website.send ( "All procedures are disabled.  Enable at least one procedure for an email to be sent." )

elif email_address_string == '':
	website.send ( "Email address not given; no email has been sent.<br>" )

else:
	# Add the body to the message and send it.
	end_message = "This is an automatically generated email, please do not respond."
	msg_body = "The included .xlsx file ({}.xlsx) contains the requested quality check data. \n\n{}".format(XLSX_FILENAME, end_message)

	if mailer.send_sfu_email("quality_check", email_address_string, "Quality Check Results", msg_body, [xlsx_file]) == 0:
		website.send ( "An email has been sent to <b>{}</b> with a full table of results. <br>Make sure <b>{}</b> is spelled correctly.<br>".format(email_address_string, email_address_string) )

	# Check if email is formatted correctly.
	if not re.match(r"[^@]+@[^@]+\.[^@]+", email_address_string):
		website.send( "Your email address (<b>{}</b>) is likely spelled incorrectly, please re-check its spelling.<br>".format(email_address_string) )

website.send ( '<br>' )
	
website.set_footer( "python version: " + sys.version)  # Print version number.
website.generate_site()  # Actually finish running the site.
