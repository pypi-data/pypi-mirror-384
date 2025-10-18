## zermelo_api_vogk
A small module to create a Zermelo accesstoken and put some data from Zermelo in dataclasses

to setup credentials import and run installAPI(schoolname, code)

to load API import loadAPI:
zermelo api = await loadAPI()

# V1.3.2 (bugfix)
 - remove uppercase form some vaknamen

# V1.3.1 (changing code of login)
  - updated loading of api
  - adding install 
  - moved config to working dir

# V1.2.6 (major refactoring of ZermeloCollection)
 - added Groep * Groepen to __init__.py
 - logging: warnings changed to debug
 - major change in ZermeloCollection using TypeVar
 - removed VakDocs
 - changed code in _io_json

# V1.1.16 (bugfix)
 - found bug: getting vakgroepen for lessons with always 2 groups is broken
 - removed filter for multiple groups -> filters now on more than 40 pupils

# V1.1.14 (refactoring & bugfixes)
 - moved zermelo API to single zermelo in _zermeloApi.py
 - added loading of SchoolInSchoolYears
 - bugfix added extra weeks in past for finding lesgroepen (re)enabled loading of time_utils
 - added filter for multiple teachers (vervanging en stagaires)
 - made appointments hashable, added loading appointment for location
 - bugfix - added scroungeSegments to Vak
 - bugfix: stagiaires grundel: "lgst"

# V1.0.10
 - made module Asynchronous

# V0.3.18 (logging update & removing of trace)

# V0.3.15
 - changed vakdoclok from subjects to choosableindepartments

# V0.3.10 - V0.3.14
 - added VakDocLoks to __init__
 - change of vakdocloks to raw data only
 - bugfix filename vakdocloks
 - testing choosablle_etc in vakdocloks
 - wrong copy of code

# V0.3.9
 - change lesgroepnaam

# V0.3.5 -> V0.3.8
 - added lokalen, removed debug from zermelo_api
 - added vakdocloks
 - bugfix: added lokalen to dataclass of branch
 - bugfix: subject in data vakdocloks is str not int

# V0.3.1 -> 0.3.4
 - start adding function to get teachers and locations for all subjects in a certain timespan.

# V0.2.18
 - added updatePackage to update remote package (linux)

# V0.2.17
 - re-enabled logger

# V0.2.16
 - found bug when running as daemon, probably: logger.
 - try without output to file

# V0.2.15
 - disabled debug mode

# V0.2.14
 - debug on for bugfixing
 - added extra debug log for filter in lesgroepen
 - edit filter to find second part of groupname in les.groups

# V0.2.13
 - New bug: loading of stamgroepen as lesgroep is broken!
 - need to update/edit filter in lesgroepen

# V0.2.12
 - removed debug for wisa and lesgroepen

# V0.2.11
 - added groep.extendentName to filter in lesgroep

# V0.2.10
 - trying to optimize lesgroepen
 - added (temp) debug to lesgroepen
 - log group

# V0.2.9
 - removed dependency of Groepen in Vakken (ot used)
 - added getName to Vak (Vakken)
 - start cleanup code

# V0.2.8
 - changed definition of Vakken and Groepen in Branch
 - added Vakken & Vak to __init__.py 

# V0.2.7
 - added response as data in getData on wrong output
 - refactoring of Appointments
  * added function: get_department_updates [doesn't work atm :( ]

# V0.2.6
 - removed linebreaks from logger.write()

# V0.2.5
 - trying getting extra data for each appointment from user
 - changed "with_id" in get_data to "from_id" and reversed functionality for better readability
 - added classmethod to Appointment to get Appointment direct from id

# V0.2.4
 - added getting appointments

# V0.2.3
 - changed getting lesgroepen only as return so not part of branch anymore
 - removed lastcheck from lesgroepen

# V0.2.2
 - bugfix lesgroepen
 - added write to logger (debug)
 - changed repr of Users

# V0.2.1
 - added datetime to each branch
 - init of branches is now only datestring, year will be determined internally

# V0.2.0
 - changed decorator from_zermelo_dict to function

# V0.1.3
- added lesgroepen

# V0.1.2
- added Vakken

# V0.1.1
  - added groepen / groups
  - First setup of vakken
  - cleanup of code

# V0.1.0: First Refactoring already:
- deleted fields.py and moved usefull functions to zermelo_api
- loading of data for (zermelo)list generalized in zermelo_api

# V0.0.8:
 - Added loading of Users (Leerlingen & Medewerkers)
 - Added backtracker to MyLogger

# V0.0.7:
- Added Loading of Branches

# V0.0.1 -> V0.0.5:
- Experimenting with creating of own package and major structure of project
