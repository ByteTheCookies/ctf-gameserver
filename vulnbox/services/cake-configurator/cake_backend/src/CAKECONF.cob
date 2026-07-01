      ******************************************************************
      *
      *  CAEKECONF 
      *  Inhouse Software for ordering bespoke cakes
      *
      *  Copyright 1992 Tailored Treats Inc.
      ******************************************************************
       IDENTIFICATION              DIVISION.
      ******************************************************************
       PROGRAM-ID.                 CAEKECONF.
       DATE-WRITTEN.               1992-01-01.
       AUTHOR.                     Horace Gopper
      ******************************************************************
       DATA                        DIVISION.
      ******************************************************************
       WORKING-STORAGE             SECTION.
      ******************************************************************
       01  WS-WELCOME.
           05  WS-CONTINUE         PIC  X(01) VALUE SPACES.
       01  WS-MAIN-MENU.
           05  WS-MENU             PIC  X(01) VALUE SPACES.
           05  WS-LOGGED-IN        PIC  9(01) VALUE 0.
           05  WS-UNAME            PIC  X(32) VALUE SPACES.
           05  WS-MSG              PIC  X(64) VALUE SPACES.
       01  WS-GET-TID.
           05  WS-TID              PIC  X(16) VALUE SPACES.
       01 WS-SCREENHELP.
           05 WS-DEL               PIC  X(79) VALUE IS ALL "-".

      ******************************************************************
       SCREEN                      SECTION.
      ******************************************************************
       01  WELCOME-SCREEN FOREGROUND-COLOR 6.
           10  VALUE "WELCOME"           
                                            BLANK SCREEN LINE 01 COL 02.
           10  DEL PIC X(79) FROM WS-DEL                 LINE 02 COL 02.
           10  VALUE "Welcome to the cake-configurator"   
                                                         LINE 04 COL 02.
           10  VALUE "For the best experience use socat to connect:"
                                                         LINE 06 COL 02.
           10  VALUE "socat -,raw,echo=0 TCP:[<IP>]:4321"   
                                               HIGHLIGHT LINE 08 COL 02.
           10  DEL PIC X(79) FROM WS-DEL                 LINE 20 COL 02.
           10  VALUE "Press enter to continue"   
                                                         LINE 22 COL 02.
           10  VALUE "Action==>"   
                                                         LINE 23 COL 02.
           10  RESPONSE-INPUT PIC X(01) TO WS-CONTINUE
                                                         LINE 23 COL 12.

       01  MAIN-MENU-SCREEN FOREGROUND-COLOR 6.
           05  MENU-SECTION.   
              10  VALUE "MAIN MENU SCREEN"  
                                            BLANK SCREEN LINE 01 COL 02.
              10  DEL PIC X(79) FROM WS-DEL              LINE 02 COL 02.
              10  VALUE "(R)EGISTER - Register a new User" 
                                                         LINE 06 COL 02.
              10  VALUE "(T)RACK - Track a order"   
                                                         LINE 08 COL 02.
              10  VALUE "(Q)UIT - Exit the program"
                                                         LINE 14 COL 02.
              10  DEL PIC X(79) FROM WS-DEL              LINE 20 COL 02.
              10  STATUS-MSG PIC X(64) FROM WS-MSG
                            HIGHLIGHT FOREGROUND-COLOR 4 LINE 21 COL 02.
              10  VALUE "Action==>"   
                                                         LINE 23 COL 02.
           05  RESPONSE-SECTION.
              10  RESPONSE-INPUT PIC X(01) USING WS-MENU
                                               HIGHLIGHT LINE 23 COL 12.
           05  LOGGEDOUT-SECTION.
              10  VALUE "(L)OGIN - User Login"          
                                                         LINE 04 COL 02.
           05  LOGGEDIN-SECTION.
              10  VALUE "(O)RDER - Order your custom cake"
                                                         LINE 10 COL 02.
              10  VALUE "(V)IEW - View all your cake orders"
                                                         LINE 12 COL 02.
              10  VALUE "Logged in as: "                 
                                               HIGHLIGHT LINE 19 COL 02.
              10  USER-INFO PIC X(32) FROM WS-UNAME      
                                               HIGHLIGHT LINE 19 COL 16.

       01  GET-TID-SCREEN FOREGROUND-COLOR 6.
           10  VALUE "Enter Tracking-ID:" 
                                            BLANK SCREEN LINE 04 COL 02.
           10  RESPONSE-INPUT PIC X(16) TO WS-TID 
                                                         LINE 05 COL 02.

       01  EOP-INDICATOR FOREGROUND-COLOR 0.
           10  VALUE "EOPEOPEOPEOPEOPEOPEOPEOPEOPEOPEOPEOPEOPEOP"
                                                         LINE 24 COL 01.

      ******************************************************************
       PROCEDURE                   DIVISION.
      ******************************************************************
           DISPLAY WELCOME-SCREEN
           DISPLAY EOP-INDICATOR
           ACCEPT WELCOME-SCREEN
           PERFORM UNTIL WS-MENU IS EQUAL TO "Q"
             EVALUATE WS-MENU
               WHEN "L"
                   MOVE SPACES TO WS-MENU
                   CALL "LOGIN" USING WS-UNAME WS-MSG
                   IF WS-UNAME IS NOT EQUAL TO SPACES 
                     MOVE 1 TO WS-LOGGED-IN
                   END-IF
               WHEN "R"
                   MOVE SPACES TO WS-MENU
                   CALL "REGISTER" USING WS-MSG
               WHEN "O"
                   MOVE SPACES TO WS-MENU
                   CALL "CAKEORDER" USING WS-UNAME WS-MSG
               WHEN "T"
                   MOVE SPACES TO WS-MENU 
                   DISPLAY GET-TID-SCREEN
                   DISPLAY EOP-INDICATOR
                   ACCEPT GET-TID-SCREEN
                   CALL "TRACKVIEW" USING WS-TID WS-MSG
               WHEN "V"
                   MOVE SPACES TO WS-MENU 
                   CALL "ORDERVIEW" USING WS-UNAME WS-MSG
               WHEN OTHER DISPLAY MENU-SECTION
                   IF WS-LOGGED-IN IS EQUAL TO 0 
                     DISPLAY LOGGEDOUT-SECTION
                   END-IF
                   IF WS-LOGGED-IN IS EQUAL TO 1 
                     DISPLAY LOGGEDIN-SECTION
                   END-IF
                   DISPLAY RESPONSE-SECTION
                   DISPLAY EOP-INDICATOR
                   ACCEPT RESPONSE-SECTION
                   MOVE SPACES TO WS-MSG
           END-PERFORM.
           STOP RUN.
