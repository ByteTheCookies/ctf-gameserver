build: vulnify.c
	gcc -o vulnify -no-pie -fstack-protector -static vulnify.c && strip -s vulnify

debug: vulnify.c
	gcc -o vulnify -Wno-format-truncation -Wall -Wextra -Werror vulnify.c

