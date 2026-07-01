      ******************************************************************
      *
      *  LOGIN 
      *
      *  Copyright 1992 Tailored Treats Inc.
      ******************************************************************
       IDENTIFICATION              DIVISION.
      ******************************************************************
       PROGRAM-ID.                 LOGIN.
      ******************************************************************
       DATA                        DIVISION.
      ******************************************************************
       WORKING-STORAGE SECTION.
      ******************************************************************
       EXEC SQL INCLUDE SQLCA END-EXEC. 
       01  WS-LOGIN.
           05 WS-SUCCESS          PIC X(01) VALUE "F".
           05 WS-UNAME            PIC X(32) VALUE SPACES.
           05 WS-PW               PIC X(32) VALUE SPACES.
           05 WS-RESPONSE         PIC X(01) VALUE "C".
           05 WS-MSG              PIC X(32) VALUE "Please login".
       01 WS-SCREENHELP.
           05 WS-DEL              PIC  X(79) VALUE IS ALL "-".

       01  SQL-DS                 PIC X(64).
       01  SQL-UNAME              PIC X(32) VALUE SPACES.
       EXEC SQL VAR SQL-UNAME IS VARCHAR(32) END-EXEC.
       01  SQL-PW                 PIC X(32) VALUE SPACES.
       EXEC SQL VAR SQL-PW IS VARCHAR(32) END-EXEC.
       01  SQL-CNT                PIC 9(04).

      ******************************************************************
       LINKAGE SECTION.
      ******************************************************************
       01  LNK-UNAME              PIC X(32).
       01  LNK-MSG                PIC X(32).
       01  LNK-PUF                PIC X(01).
       WORKING-STORAGE SECTION.

      ******************************************************************
       SCREEN                      SECTION.
      ******************************************************************
       01  LOGIN-SCREEN FOREGROUND-COLOR 6.
           10  VALUE "LOGIN       SCREEN"   BLANK SCREEN LINE 01 COL 02.
           10  DEL PIC X(79) FROM WS-DEL                 LINE 02 COL 02.
           10  VALUE "Username:"                           
                                                         LINE 04 COL 02.
           10  USERNAME-INPUT PIC X(32) TO WS-UNAME       
                                                         LINE 04 COL 16.
           10  VALUE "Password:"                          
                                                         LINE 06 COL 02.
           10  PWD-INPUT PIC X(32) TO WS-PW
                                                         LINE 06 COL 16.
           10  DEL PIC X(79) FROM WS-DEL                 LINE 20 COL 02.
           10  LOGIN-MSG PIC X(64) FROM WS-MSG
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
       PROCEDURE                   DIVISION USING LNK-UNAME LNK-MSG.
      ******************************************************************
           PERFORM FOREVER
             DISPLAY LOGIN-SCREEN
             DISPLAY EOP-INDICATOR
             ACCEPT LOGIN-SCREEN
             EVALUATE WS-RESPONSE
                WHEN "C"
                  PERFORM LOGIN-USER
                WHEN "M"
                  GOBACK
                WHEN OTHER
                  MOVE SPACES TO WS-RESPONSE
                  MOVE "Invalid action" TO WS-MSG
             END-EVALUATE
             IF WS-SUCCESS = "T" 
             THEN
               MOVE "login successful" TO LNK-MSG
               MOVE WS-UNAME TO LNK-UNAME
               GOBACK
             END-IF
           END-PERFORM.
      ******************************************************************

      ******************************************************************
       LOGIN-USER.
      ******************************************************************
           MOVE  "pgsql://cake_db:5432/app"  TO  SQL-DS.
           EXEC SQL
               CONNECT TO :SQL-DS USER cake_user USING ilovecake
           END-EXEC.
           IF  SQLCODE NOT = ZERO PERFORM SQL-ERROR EXIT PARAGRAPH.
           
           PERFORM SQL-CHECK-USER.
           
           EXEC SQL
               DISCONNECT
           END-EXEC.
           EXIT PARAGRAPH.
      ******************************************************************

      ******************************************************************
       SQL-CHECK-USER.
      ******************************************************************
           MOVE WS-UNAME TO SQL-UNAME.
           MOVE WS-PW TO SQL-PW.
           
           EXEC SQL
              SELECT COUNT(*) INTO :SQL-CNT FROM USERS
                WHERE USERNAME = :SQL-UNAME AND PASSWORD = :SQL-PW
           END-EXEC.
           IF SQLCODE NOT = ZERO PERFORM SQL-ERROR EXIT PARAGRAPH.
           IF SQL-CNT = 0 MOVE "Invalid username or password" TO WS-MSG.
           IF SQL-CNT = 1 MOVE "T" TO WS-SUCCESS.
           EXIT PARAGRAPH.
      ******************************************************************

      ******************************************************************
       SQL-ERROR.
      ******************************************************************
           MOVE SQLERRMC TO WS-MSG
           EXIT PARAGRAPH.
      ******************************************************************
