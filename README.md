# BEIC
Tools developed and used for BEIC (Biblioteca Europea di Informazione e Cultura)
as part of its partnership with Wikimedia Italia (http://wikimedia.it/).

More information on BEIC: http://www.beic.it/

Main pages where to read more about this project and follow it:
* https://it.wikipedia.org/wiki/Progetto:GLAM/BEIC
* https://www.wikidata.org/wiki/Q18152337#sitelinks-wikipedia

## BEIC_pid_list.py

To make a nice table from a list of PID numbers:

* install the dependencies with your package manager (usually `python python-requests python-kitchen python-lxml`);
* save the list of PID numbers one per line in a file named `BEIC-pids.txt`;
* remove the pywikibot import lines from `BEIC_pid_upload.py`;
* run the program with no arguments.