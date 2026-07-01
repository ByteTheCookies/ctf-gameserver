      ******************************************************************
      *
      *  TRACKVIEW 
      *
      *  Copyright 1992 Tailored Treats Inc.
      ******************************************************************
       IDENTIFICATION              DIVISION.
      ******************************************************************
       PROGRAM-ID.                 TRACKVIEW.
      ******************************************************************
       DATA                        DIVISION.
      ******************************************************************
       WORKING-STORAGE SECTION.
      ******************************************************************
       EXEC SQL INCLUDE SQLCA END-EXEC. 
       01  WS-TRACKVIEW.
           10 WS-RESPONSE       PIC X(01) VALUE "M".
           10 WS-CAKESIZE       PIC X(01) VALUE SPACES.
           10 WS-FLAVOR         PIC X(64) VALUE SPACES.
           10 WS-TOPPINGS       PIC X(32) VALUE SPACES.
           10 WS-CUSTOMTXT      PIC X(32) VALUE SPACES.
           10 WS-COMMENT        PIC X(64) VALUE SPACES.
           10 WS-PRICE          PIC 9(02),9(02)$ VALUE 0.
           10 WS-MSG            PIC X(64) VALUE SPACES.
       01 WS-SCREENHELP.
           10 WS-DEL            PIC X(79) VALUE IS ALL "-".

       *>  SQL Variables
       01  SQL-DS               PIC X(64).
       01  SQL-UNAME            PIC X(32) VALUE SPACES.
       EXEC SQL VAR SQL-UNAME IS VARCHAR(32) END-EXEC.
       01  SQL-CAKESIZE         PIC X(1) VALUE SPACES.
       EXEC SQL VAR SQL-CAKESIZE IS VARCHAR(1) END-EXEC.
       01  SQL-FLAVOR           PIC X(64) VALUE SPACES.
       EXEC SQL VAR SQL-FLAVOR IS VARCHAR(64) END-EXEC.
       01  SQL-TOPPINGS         PIC X(32) VALUE SPACES.
       EXEC SQL VAR SQL-TOPPINGS IS VARCHAR(32) END-EXEC.
       01  SQL-CUSTOMTXT        PIC X(32) VALUE SPACES.
       EXEC SQL VAR SQL-CUSTOMTXT IS VARCHAR(32) END-EXEC.
       01  SQL-COMMENT          PIC X(64) VALUE SPACES.
       EXEC SQL VAR SQL-COMMENT IS VARCHAR(64) END-EXEC.
       01  SQL-PRICE            PIC 9(04).
       01  SQL-TID              PIC X(16) VALUE SPACES.
       EXEC SQL VAR SQL-TID IS VARCHAR(16) END-EXEC.

      ******************************************************************
       LINKAGE SECTION.
      ******************************************************************
       01  LNK-TRACKINGID       PIC X(16).
       01  LNK-MSG              PIC X(64).
       01  LNK-PUF              PIC X(01).
       WORKING-STORAGE SECTION.

      ******************************************************************
       SCREEN                      SECTION.
      ******************************************************************
       01  TRACKVIEW-SCREEN FOREGROUND-COLOR 6.
           10  VALUE "TRACKING    SCREEN"   BLANK SCREEN LINE 01 COL 02.
           10  DEL PIC X(79) FROM WS-DEL                 LINE 02 COL 02.
           10  VALUE "Tracking-ID:"                           
                                                         LINE 04 COL 02.
           10  TID PIC X(16) FROM LNK-TRACKINGID       
                                                         LINE 04 COL 16.
           10  VALUE "Size:"                          
                                                         LINE 06 COL 02.
           10  CAKESIZE PIC X(01) FROM WS-CAKESIZE
                                                         LINE 06 COL 16.
           10  VALUE "Flavor:"                          
                                                         LINE 08 COL 02.
           10  FLAVOR PIC X(64) FROM WS-FLAVOR
                                                         LINE 08 COL 16.
           10  VALUE "Toppings:"                          
                                                         LINE 10 COL 02.
           10  TOPPINGS PIC X(32) FROM WS-TOPPINGS
                                                         LINE 10 COL 16.
           10  VALUE "Custom text:"                          
                                                         LINE 12 COL 02.
           10  CUSTOMTXT PIC X(32) FROM WS-CUSTOMTXT
                                                         LINE 12 COL 16.
           10  VALUE "Comment:"                          
                                                         LINE 14 COL 02.
           10  COMMENT PIC X(64) FROM WS-COMMENT
                                                         LINE 14 COL 16.
           10  VALUE "Price:"                          
                                                         LINE 16 COL 02.
           10  PRICE PIC 9(02),9(02)$ FROM WS-PRICE
                                           HIGHLIGHT     LINE 16 COL 16.
           10  DEL PIC X(79) FROM WS-DEL                 LINE 20 COL 02.
           10  ORDER-MESSAGE PIC X(64) FROM WS-MSG
                            HIGHLIGHT FOREGROUND-COLOR 4 LINE 21 COL 02. 
           10  VALUE "(M)ENU"   
                                                         LINE 22 COL 02.
           10  VALUE "Action==>"   
                                                         LINE 23 COL 02.
           10  RESPONSE-INPUT PIC X(01) TO WS-RESPONSE
                                                         LINE 23 COL 12.
       01  EOP-INDICATOR.
           10  VALUE "EOPEOPEOPEOPEOPEOPEOPEOPEOPEOPEOPEOPEOPEOP"
                                      FOREGROUND-COLOR 0 LINE 20 COL 01.

      ******************************************************************
       PROCEDURE                  DIVISION USING LNK-TRACKINGID LNK-MSG.
      ******************************************************************
           PERFORM SQL-FIND-ORDER
           PERFORM FOREVER
             DISPLAY TRACKVIEW-SCREEN
             DISPLAY EOP-INDICATOR
             ACCEPT TRACKVIEW-SCREEN
             IF WS-RESPONSE = "M"
               GOBACK
             END-IF
           END-PERFORM.
      ******************************************************************

      ******************************************************************
       SQL-FIND-ORDER.
      ******************************************************************
           MOVE  "pgsql://cake_db:5432/app"  TO  SQL-DS.
           EXEC SQL
               CONNECT TO :SQL-DS USER cake_user USING ilovecake
           END-EXEC.
           IF  SQLCODE NOT = ZERO PERFORM SQL-ERROR-RTN EXIT PARAGRAPH.
           
           MOVE LNK-TRACKINGID TO SQL-TID.           
           EXEC SQL
              SELECT CAKESIZE, FLAVOR, TOPPINGS, CUSTOM_TEXT, COMMENT,
              PRICE INTO :SQL-CAKESIZE, :SQL-FLAVOR, :SQL-TOPPINGS,
              :SQL-CUSTOMTXT, _:SQL-COMMENT, :SQL-PRICE
              FROM ORDERS WHERE ID = :SQL-TID
           END-EXEC.

           IF SQLCODE NOT = ZERO PERFORM SQL-ERROR-RTN EXIT PARAGRAPH.
           EXEC SQL
               DISCONNECT
           END-EXEC.

           MOVE SQL-CAKESIZE TO WS-CAKESIZE.
           MOVE SQL-FLAVOR TO WS-FLAVOR.
           MOVE SQL-TOPPINGS TO WS-TOPPINGS.
           MOVE SQL-CUSTOMTXT TO WS-CUSTOMTXT.
           MOVE SQL-COMMENT TO WS-COMMENT.
           MOVE SQL-PRICE TO WS-PRICE.
           EXIT PARAGRAPH.
      ******************************************************************

      ******************************************************************
       SQL-ERROR-RTN.
      ******************************************************************
           MOVE SQLERRMC TO LNK-MSG
           GOBACK.
      ******************************************************************
