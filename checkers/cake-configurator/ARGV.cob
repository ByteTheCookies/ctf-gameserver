       IDENTIFICATION DIVISION.
       PROGRAM-ID. show-argv.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-TRACKINGID.
           10 WS-UID      PIC 9(04).
           10 WS-RAND     PIC X(12).
       01 WS-RNG.
           10 WS-NDX      PIC S9(02) COMP.
           10 WS-RANDI    PIC 9(02).
           10 WS-ALPH     PIC X(26) VALUES "ABCDEFGHIJKLMNOPQRSTUVWXYZ".
       01 WS-STRARR.
           02 WS-ARR OCCURS 12 TIMES.
             05 WS-CSB    PIC X(01).
       01 WS-SEED         PIC 9(04).


       PROCEDURE DIVISION.
           ACCEPT WS-UID
           ACCEPT WS-SEED

           COMPUTE WS-RANDI = FUNCTION RANDOM(WS-SEED)*26 + 1
           PERFORM VARYING WS-NDX FROM 1 BY 1 UNTIL WS-NDX>12
             COMPUTE WS-RANDI = Function RANDOM*26 + 1
             STRING WS-ALPH(WS-RANDI:1) INTO WS-CSB(WS-NDX)
           END-PERFORM.
           MOVE WS-STRARR TO WS-RAND.
           DISPLAY WS-TRACKINGID
           .
