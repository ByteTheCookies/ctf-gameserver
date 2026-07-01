SERVICE := cake-configurator
DESTDIR ?= dist_root
SERVICEDIR ?= /srv/$(SERVICE)

.PHONY: build install

build:
	echo nothing to build

install: build
	mkdir -p $(DESTDIR)$(SERVICEDIR)
	yq -y 'del(.services."cake_backend_deps") | del(.services."cake_cleanup_deps")' docker-compose.yml > $(DESTDIR)$(SERVICEDIR)/docker-compose.yml

	
	mkdir -p $(DESTDIR)$(SERVICEDIR)/cake_backend
	cp -r cake_backend/* $(DESTDIR)$(SERVICEDIR)/cake_backend/
	
	mkdir -p $(DESTDIR)$(SERVICEDIR)/db
	cp -r db/* $(DESTDIR)$(SERVICEDIR)/db/

	mkdir -p $(DESTDIR)$(SERVICEDIR)/cleanup
	cp -r cleanup/* $(DESTDIR)$(SERVICEDIR)/cleanup/

	mkdir -p $(DESTDIR)/etc/systemd/system/faustctf.target.wants/
	ln -s /etc/systemd/system/docker-compose@.service $(DESTDIR)/etc/systemd/system/faustctf.target.wants/docker-compose@$(SERVICE).service

