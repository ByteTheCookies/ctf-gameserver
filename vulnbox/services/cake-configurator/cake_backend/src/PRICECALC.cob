      ******************************************************************
      *
      *  PRICECALC 
      *
      *  Copyright 1992 Tailored Treats Inc.
      ******************************************************************
       IDENTIFICATION              DIVISION.
      ******************************************************************
       PROGRAM-ID.                 PRICECALC.
      ******************************************************************
       DATA                        DIVISION.
      ******************************************************************
       WORKING-STORAGE SECTION.
      ******************************************************************
       
       01  WS-PRICECALC.
           10 WS-PRICE                PIC 9(04) VALUE 0.
           10 WS-TOPPINGC             PIC 9(02) VALUE 0.
           10 WS-TXTC                 PIC 9(02) VALUE 0.
       01  WS-PRICECONF.
           05 WS-SIZES.
             10 WS-SMALL              PIC 9(04) VALUE 1000.
             10 WS-MEDIUM             PIC 9(04) VALUE 1500.
             10 WS-LARGE              PIC 9(04) VALUE 2000.
           10 WS-LETTER               PIC 9(04) VALUE 25.
           10 WS-TOPING               PIC 9(04) VALUE 200.

      ******************************************************************
       LINKAGE SECTION.
      ******************************************************************
       01  LNK-PRICE                  PIC 9(04).
       01  LNK-CAKESIZE               PIC X(01).
       01  LNK-TOPPINGS               PIC X(32).
       01  LNK-CUSTOMTXT              PIC X(32).

      ******************************************************************
       PROCEDURE DIVISION 
           USING LNK-PRICE LNK-CAKESIZE LNK-TOPPINGS LNK-CUSTOMTXT.
      ******************************************************************
           EVALUATE LNK-CAKESIZE
           WHEN "s"
             MOVE WS-SMALL TO WS-PRICE
           WHEN "m"
             MOVE WS-MEDIUM TO WS-PRICE
           WHEN OTHER
             MOVE WS-LARGE TO WS-PRICE
           END-EVALUATE
           
           INSPECT LNK-CUSTOMTXT TALLYING WS-TXTC FOR ALL SPACES
           COMPUTE WS-PRICE = (32 - WS-TXTC) * WS-LETTER + WS-PRICE

           IF LNK-TOPPINGS IS EQUAL TO SPACES
             MOVE WS-PRICE TO LNK-PRICE
             GOBACK
           END-IF
           INSPECT LNK-TOPPINGS TALLYING WS-TOPPINGC FOR ALL ","
           ADD 1 TO WS-TOPPINGC
           COMPUTE WS-PRICE = WS-TOPPINGC * WS-TOPING + WS-PRICE
           MOVE WS-PRICE TO LNK-PRICE
           GOBACK.
      ******************************************************************
