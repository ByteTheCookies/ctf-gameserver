      ******************************************************************
      *
      *  REGISTER 
      *
      *  Copyright 1992 Tailored Treats Inc.
      ******************************************************************
       IDENTIFICATION              DIVISION.
      ******************************************************************
       PROGRAM-ID.                 REGISTER.
      ******************************************************************
       DATA                        DIVISION.
      ******************************************************************
       WORKING-STORAGE SECTION.
      ******************************************************************
       EXEC SQL INCLUDE SQLCA END-EXEC. 
       01  WS-REGISTRATION.
           05 WS-SUCCESS          PIC X(01).
           05 WS-REGNAME          PIC X(32) VALUE SPACES.
           05 WS-PW               PIC X(32) VALUE SPACES.
           05 WS-RESPONSE         PIC X(01) VALUE "C".
           05 WS-MSG              PIC X(64).
       01 WS-SCREENHELP.
           05 WS-DEL              PIC  X(79) VALUE IS ALL "-".
       01  SQL-DS                 PIC X(64).
       01  SQL-UNAME              PIC X(32) VALUE SPACES.
       EXEC SQL VAR SQL-UNAME IS VARCHAR(32) END-EXEC.
       01  SQL-PW                 PIC X(32) VALUE SPACES.
       EXEC SQL VAR SQL-PW IS VARCHAR(32) END-EXEC.

      ******************************************************************
       LINKAGE SECTION.
      ******************************************************************
       01  LNK-MSG                PIC X(64).
       01  LNK-PUF                PIC X(1).
       WORKING-STORAGE SECTION.

      ******************************************************************
       SCREEN                      SECTION.
      ******************************************************************
       01  REGISTER-SCREEN FOREGROUND-COLOR 6.
           10  VALUE "REGISTER    SCREEN"   BLANK SCREEN LINE 01 COL 02.
           10  DEL PIC X(79) FROM WS-DEL                 LINE 02 COL 02.
           10  VALUE "Username:"                           
                                                         LINE 04 COL 02.
           10  USERNAME-INPUT PIC X(32) TO WS-REGNAME       
                                                         LINE 04 COL 16.
           10  VALUE "Password:"                          
                                                         LINE 06 COL 02.
           10  PWD-INPUT PIC X(32) TO WS-PW
                                                         LINE 06 COL 16.
           10  DEL PIC X(79) FROM WS-DEL                 LINE 20 COL 02.
           10  REGISTER-MESSAGE PIC X(64) FROM WS-MSG
                            HIGHLIGHT FOREGROUND-COLOR 4 LINE 21 COL 02. 
           10  VALUE "(C)ONTINUE, (M)ENU"   
                                                         LINE 22 COL 02.
           10  VALUE "Action==>"   
                                                         LINE 23 COL 02.
           10  RESPONSE-INPUT PIC X(01) USING WS-RESPONSE
                                                         LINE 23 COL 12.
       01  EOP-INDICATOR FOREGROUND-COLOR 0.
           10  VALUE "EOPEOPEOPEOPEOPEOPEOPEOPEOPEOPEOPEOPEOPEOP"
                                                         LINE 24 COL 01.

      ******************************************************************
       PROCEDURE                   DIVISION USING LNK-MSG.
      ******************************************************************
           MOVE "F" TO WS-SUCCESS
           MOVE "Please register" TO WS-MSG
           PERFORM FOREVER
             DISPLAY REGISTER-SCREEN
             DISPLAY EOP-INDICATOR
             ACCEPT REGISTER-SCREEN
             EVALUATE WS-RESPONSE 
                WHEN "C"
                   IF WS-REGNAME IS EQUAL TO SPACES
                   THEN
                      MOVE "Invalid username" TO WS-MSG
                   ELSE
                      PERFORM INSERT-USER
                   END-IF
               WHEN "M"
                  GOBACK
                WHEN OTHER
                  MOVE SPACES TO WS-RESPONSE
                  MOVE "Invalid action" TO WS-MSG
             END-EVALUATE
             IF WS-SUCCESS = "T" 
                MOVE "Registration successful" TO LNK-MSG
                GOBACK
             END-IF
           END-PERFORM.
      ******************************************************************

      ******************************************************************
       INSERT-USER.
      ******************************************************************
           MOVE  "pgsql://cake_db:5432/app"  TO  SQL-DS.
           EXEC SQL
               CONNECT TO :SQL-DS USER cake_user USING ilovecake
           END-EXEC.
           IF  SQLCODE NOT = ZERO PERFORM SQL-ERROR EXIT PARAGRAPH.

           PERFORM SQL-INSERT-USER.

           EXEC SQL
               DISCONNECT
           END-EXEC.
           EXIT PARAGRAPH.
      ******************************************************************

      ******************************************************************
       SQL-INSERT-USER.
      ******************************************************************
           MOVE WS-REGNAME TO SQL-UNAME.
           MOVE WS-PW TO SQL-PW.
           
           EXEC SQL
              INSERT INTO USERS (USERNAME, PASSWORD)
                VALUES(:SQL-UNAME, :SQL-PW)
           END-EXEC.
           IF  SQLCODE NOT = ZERO PERFORM SQL-ERROR EXIT PARAGRAPH.
           IF  SQLCODE = ZERO MOVE "T" TO WS-SUCCESS.
           EXIT PARAGRAPH.
      ******************************************************************

      ******************************************************************
       SQL-ERROR.
      ******************************************************************
           MOVE SQLERRMC TO WS-MSG
           EXIT PARAGRAPH.
      ******************************************************************
