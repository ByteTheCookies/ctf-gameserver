COB_FILES := $(wildcard *.cob)
ENTRY_FILE := CAKECONF.cob
DEP_FILES := $(filter-out $(ENTRY_FILE), $(COB_FILES))

COBSQL_FILES := $(COB_FILES:.cob=.cobsql)
ENTRY_COBSQL := $(ENTRY_FILE:.cob=.cobsql)
DEP_COBSQL := $(DEP_FILES:.cob=.cobsql)

DEP_OBJECTS := $(DEP_COBSQL:.cobsql=.o)
ENTRY_EXECUTABLE := CAKECONF

.PHONY: all clean

all: $(ENTRY_EXECUTABLE)

# Rule to create .cobsql from .cob
%.cobsql: %.cob
	gixsql $< $@ -e
	./gixfix.py $@

# Dependencies: build .o files (no -x)
%.o: %.cobsql
	cobc -c $< -I /usr/share/gixsql/copy -L /lib/ -lgixsql

# Entry point: build final executable with -x and link deps
$(ENTRY_EXECUTABLE): $(DEP_OBJECTS) $(ENTRY_COBSQL)
	cobc -x -o $@ $(ENTRY_COBSQL) $(DEP_OBJECTS) -I /usr/share/gixsql/copy -L /lib/ -lgixsql

clean:
	rm -f $(COBSQL_FILES) $(DEP_OBJECTS) $(ENTRY_EXECUTABLE)
