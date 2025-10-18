# cfpsec
CFPsec is program to list Call For Papers or upcoming Hacking/Security Conferences based on cfptime.org website.

### Copyright (C)  2025 Alexandre Borges <reverseexploit at proton dot  me>

      This program is free software: you can redistribute it and/or modify
      it under the terms of the GNU General Public License as published by
      the Free Software Foundation, either version 3 of the License, or
      (at your option) any later version.

      This program is distributed in the hope that it will be useful,
      but WITHOUT ANY WARRANTY; without even the implied warranty of
      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
      GNU General Public License for more details.

      See GNU Public License on <http://www.gnu.org/licenses/>.
      
### Current Version: 1.5
 
CFPsec has been tested on Ubuntu and Windows 11. Likely, it also works on other 
operating systems. Before using CFPsec, execute:

        $ Install Python 3.9 or newer.
        $ pip install cfpsec
 
### USAGE

To use the CFPsec, execute the command as shown below:

      # cfpsec.py --cfp
      # cfpsec.py --up

      usage: python cfpsec.py [--cfp] [--up]

      CFPsec lists Call For Papers or upcoming Hacking/Security Conferences
      based on cfptime.org website.

      options:
      -h, --help  show this help message and exit
      --cfp       List Call For Papers of Hacking/Security Conferences.
      --up        List all upcoming Hacking/Security Conferences.
 
### HISTORY


Version 1.5:

      This version:
      
            * Fixes the --cfp option to reflect a structural change on the cfptime.org. 

Version 1.4:

      This version:
      
            * Presents a full refactoring of the code. 

Version 1.3:

      This version:
      
            * Fixes have been introduced. 
            * Slight changes in the Python code. 

Version 1.2:

      This version:
      
            * Small fixes have been introduced. 
            * Small structure change. 

Version 1.0.2:

      This version:
      
            * Introduces a small fix. 

Version 1.0.1:

      This version:
      
            * Introduces the possibility to install the cfpsec by using 
            the Python pip module: pip install cfpsec. 

Version 1.0:

      This version:
      
            * Includes the -c option to list Call for Papers of Hacking/Security Conferences. 
            * Includes the -u option to list upcoming Hacking/Security Conferences.
