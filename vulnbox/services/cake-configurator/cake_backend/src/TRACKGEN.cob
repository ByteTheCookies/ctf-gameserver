      ******************************************************************
      *
      *  TRACKGEN 
      *
      *  Copyright 1992 Tailored Treats Inc.
      ******************************************************************
       IDENTIFICATION              DIVISION.
      ******************************************************************
       PROGRAM-ID.                 TRACKGEN.
      ******************************************************************
       DATA                        DIVISION.
      ******************************************************************
       WORKING-STORAGE SECTION.
      ******************************************************************
       EXEC SQL INCLUDE SQLCA END-EXEC. 
       01  WS-TRACKINGID.
           10 WS-UID      PIC 9(05).
           10 WS-RAND     PIC X(11).
       01 WS-TIME.
           10 WS-MICROSEC PIC 9(04).
           10 WS-SEC      PIC 9(02).
           10 WS-MIN      PIC 9(02).
           10 WS-HOUR     PIC 9(02).
       01 WS-RNG.
           10 WS-NDX      PIC S9(02) COMP.
           10 WS-RANDI    PIC 9(02).
           10 WS-ALPH     PIC X(36) VALUES 
           "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789".
       01 WS-STRARR.
           02 WS-ARR OCCURS 12 TIMES.
             05 WS-CSB    PIC X(01).

       01  SQL-DS         PIC X(64).
       01  SQL-UNAME      PIC X(32) VALUE SPACES.
       EXEC SQL VAR SQL-UNAME IS VARCHAR(32) END-EXEC.
       01  SQL-UID        PIC 9(05).

      ******************************************************************
       LINKAGE SECTION.
      ******************************************************************
       01  LNK-TID        PIC X(16).
       01  LNK-UNAME      PIC X(32).
       01  LNK-MSG        PIC X(64).
       01  LNK-PUF        PIC X(01).
       WORKING-STORAGE SECTION.

      ******************************************************************
       PROCEDURE               DIVISION USING LNK-TID LNK-UNAME LNK-MSG.
      ******************************************************************
           PERFORM SQL-GETUID.

           ACCEPT WS-TIME FROM TIME
           COMPUTE WS-RANDI = FUNCTION RANDOM(WS-MICROSEC)*26 + 1
           PERFORM VARYING WS-NDX FROM 1 BY 1 UNTIL WS-NDX>11
             COMPUTE WS-RANDI = Function RANDOM*36 + 1
             STRING WS-ALPH(WS-RANDI:1) INTO WS-CSB(WS-NDX)
           END-PERFORM.
           MOVE WS-STRARR TO WS-RAND.

           MOVE WS-TRACKINGID TO LNK-TID
           GOBACK.
      ******************************************************************

      ******************************************************************
       SQL-GETUID.
      ******************************************************************
           MOVE LNK-UNAME TO SQL-UNAME.
           
           PERFORM SQL-CONNECT.
           EXEC SQL
              SELECT ID INTO :SQL-UID FROM USERS
                WHERE USERNAME = :SQL-UNAME
           END-EXEC.
           IF SQLCODE NOT = ZERO PERFORM SQL-ERROR-RTN.
           MOVE SQL-UID TO WS-UID.
           EXEC SQL
               DISCONNECT
           END-EXEC.
      ******************************************************************

      ******************************************************************
       SQL-CONNECT.
      ******************************************************************
           MOVE  "pgsql://cake_db:5432/app"  TO  SQL-DS.
           EXEC SQL
               CONNECT TO :SQL-DS USER cake_user USING ilovecake
           END-EXEC.
           IF  SQLCODE NOT = ZERO PERFORM SQL-ERROR-RTN.
      ******************************************************************

      ******************************************************************
       SQL-ERROR-RTN.
      ******************************************************************
           MOVE SQLERRMC TO LNK-MSG
           GOBACK.
      ******************************************************************
