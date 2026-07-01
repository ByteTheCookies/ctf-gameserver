      ******************************************************************
      *
      *  CAKEORDER 
      *
      *  Copyright 1992 Tailored Treats Inc.
      ******************************************************************
       IDENTIFICATION              DIVISION.
      ******************************************************************
       PROGRAM-ID.                 CAKEORDER.
      ******************************************************************
       DATA                        DIVISION.
      ******************************************************************
       WORKING-STORAGE SECTION.
      ******************************************************************
       EXEC SQL INCLUDE SQLCA END-EXEC. 
       
       01  WS-CAKEORDER.
           10 WS-CAKESIZE            PIC X(01) VALUE SPACES.
           10 WS-FLAVOR              PIC X(64) VALUE SPACES.
           10 WS-TOPPINGS            PIC X(32) VALUE SPACES.
           10 WS-CUSTOMTXT           PIC X(32) VALUE SPACES.
           10 WS-COMMENT             PIC X(64) VALUE SPACES.
           10 WS-TRACKINGID          PIC X(16) VALUE SPACES.
           10 WS-PRICE               PIC 9(04) VALUE 0.
           10 WS-RESPONSE            PIC X(01) VALUE SPACES.
           10 WS-SUCCESS             PIC X(01) VALUE "F".
           10 WS-MSG                 PIC X(64) VALUE "Place your order".
       01 WS-SCREENHELP.
           10 WS-DEL                 PIC X(79) VALUE IS ALL "-".

       *>  SQL Variables
       01  SQL-DS                    PIC  X(64).
       01  SQL-UNAME                 PIC  X(32) VALUE SPACES.
       EXEC SQL VAR SQL-UNAME IS VARCHAR(32) END-EXEC.
       01  SQL-CAKESIZE              PIC  X(1) VALUE SPACES.
       EXEC SQL VAR SQL-CAKESIZE IS VARCHAR(1) END-EXEC.
       01  SQL-FLAVOR                PIC  X(64) VALUE SPACES.
       EXEC SQL VAR SQL-FLAVOR IS VARCHAR(64) END-EXEC.
       01  SQL-TOPPINGS              PIC  X(32) VALUE SPACES.
       EXEC SQL VAR SQL-TOPPINGS IS VARCHAR(32) END-EXEC.
       01  SQL-CUSTOMTXT             PIC  X(32) VALUE SPACES.
       EXEC SQL VAR SQL-CUSTOMTXT IS VARCHAR(32) END-EXEC.
       01  SQL-COMMENT               PIC  X(64) VALUE SPACES.
       EXEC SQL VAR SQL-COMMENT IS VARCHAR(64) END-EXEC.
       01  SQL-PRICE                 PIC  9(04) VALUE 0.
       01  SQL-TID                   PIC  X(16) VALUE SPACES.
       EXEC SQL VAR SQL-TID IS VARCHAR(16) END-EXEC.

      ******************************************************************
       LINKAGE SECTION.
      ******************************************************************
       01  LNK-UNAME                 PIC  X(32).
       01  LNK-MSG                   PIC  X(64).
       01  LNK-PUF                   PIC  X(1).
       WORKING-STORAGE SECTION.

      ******************************************************************
       SCREEN                      SECTION.
      ******************************************************************
       01  ORDER-SCREEN FOREGROUND-COLOR 6.
           10  VALUE "ORDER       SCREEN"   BLANK SCREEN LINE 01 COL 02.
           10  DEL PIC X(79) FROM WS-DEL                 LINE 02 COL 02.
           10  VALUE "Size(s/m/l):"                           
                                                         LINE 04 COL 02.
           10  CAKESIZE-INPUT PIC X(01) TO WS-CAKESIZE       
                                                         LINE 04 COL 16.
           10  VALUE "Flavor:"                          
                                                         LINE 06 COL 02.
           10  FLAVOR-INPUT PIC X(64) TO WS-FLAVOR
                                                         LINE 06 COL 16.
           10  VALUE "Toppings:"                          
                                                         LINE 08 COL 02.
           10  TOPPING-INPUT PIC X(32) TO WS-TOPPINGS
                                                         LINE 08 COL 16.
           10  VALUE "Custom text:"                          
                                                         LINE 10 COL 02.
           10  CUSTOMTXT-INPUT PIC X(32) TO WS-CUSTOMTXT
                                                         LINE 10 COL 16.
           10  VALUE "Comment:"                          
                                                         LINE 12 COL 02.
           10  COMMENT-INPUT PIC X(64) TO WS-COMMENT
                                                         LINE 12 COL 16.
           10  DEL PIC X(79) FROM WS-DEL                 LINE 20 COL 02.
           10  ORDER-MESSAGE PIC X(64) FROM WS-MSG
                            HIGHLIGHT FOREGROUND-COLOR 4 LINE 21 COL 02. 
           10  VALUE "(C)ONTINUE, (M)ENU"   
                                                         LINE 22 COL 02.
           10  VALUE "Action==>"   
                                                         LINE 23 COL 02.
           10  RESPONSE-INPUT PIC X(01) TO WS-RESPONSE
                                                         LINE 23 COL 12.
       01  EOP-INDICATOR.
           10  VALUE "EOPEOPEOPEOPEOPEOPEOPEOPEOPEOPEOPEOPEOPEOP"
                                      FOREGROUND-COLOR 0 LINE 20 COL 01. 


      ******************************************************************
       PROCEDURE                   DIVISION USING LNK-UNAME LNK-MSG.
      ******************************************************************
           PERFORM FOREVER
             DISPLAY ORDER-SCREEN
             DISPLAY EOP-INDICATOR
             ACCEPT ORDER-SCREEN
             EVALUATE WS-RESPONSE
             WHEN "C"
               CALL "TRACKGEN" USING WS-TRACKINGID LNK-UNAME LNK-MSG
               CALL "PRICECALC"
                 USING WS-PRICE WS-CAKESIZE WS-TOPPINGS WS-CUSTOMTXT
               PERFORM SQL-GEN-ORDER
               EVALUATE WS-SUCCESS
               WHEN "T"
                  CALL "TRACKVIEW" USING WS-TRACKINGID LNK-MSG
                  MOVE "Order created successfully!" TO LNK-MSG
                  GOBACK
               WHEN OTHER
                  MOVE "Couldnt create order. Try again." TO LNK-MSG
                  GOBACK
               END-EVALUATE
             WHEN "M"
                GOBACK
             WHEN OTHER
                MOVE SPACES TO WS-RESPONSE
                MOVE "Invalid action" TO WS-MSG
             END-EVALUATE
           END-PERFORM.
      ******************************************************************

      ******************************************************************
       SQL-GEN-ORDER.
      ******************************************************************
           MOVE  "pgsql://cake_db:5432/app"  TO  SQL-DS.
           EXEC SQL
               CONNECT TO :SQL-DS USER cake_user USING ilovecake
           END-EXEC.
           IF  SQLCODE NOT = ZERO PERFORM SQL-ERROR-RTN.
           
           MOVE LNK-UNAME TO SQL-UNAME.
           MOVE WS-TRACKINGID TO SQL-TID.
           MOVE WS-CAKESIZE TO SQL-CAKESIZE.
           MOVE WS-FLAVOR TO SQL-FLAVOR.
           MOVE WS-TOPPINGS TO SQL-TOPPINGS
           MOVE WS-CUSTOMTXT TO SQL-CUSTOMTXT
           MOVE WS-COMMENT TO SQL-COMMENT
           MOVE WS-PRICE TO SQL-PRICE

           EXEC SQL
              INSERT INTO ORDERS (ID, USERNAME, CAKESIZE, FLAVOR, 
              TOPPINGS, CUSTOM_TEXT, COMMENT, PRICE)
                VALUES(:SQL-TID, :SQL-UNAME, :SQL-CAKESIZE, :SQL-FLAVOR,
                :SQL-TOPPINGS, :SQL-CUSTOMTXT, :SQL-COMMENT, :SQL-PRICE)
           END-EXEC.
           IF SQLCODE = ZERO MOVE "T" TO WS-SUCCESS.
           IF SQLCODE NOT = ZERO MOVE "F" TO WS-SUCCESS.
           EXEC SQL
               DISCONNECT
           END-EXEC.
           EXIT PARAGRAPH.
      ******************************************************************

      ******************************************************************
       SQL-ERROR-RTN.
      ******************************************************************
           MOVE SQLERRMC TO LNK-MSG
           GOBACK.
      ******************************************************************