# cc-stompbox desktop emulator
#
#   make deps   fetch MOD's cc-master and cc-slave at the tested commits (into ../deps)
#   make        build fakebox (the stompbox) and controlchaind (MOD's master)
#
# MOD's code is LGPL-3.0 and is fetched, not copied into this repo.

DEPS        ?= ../deps
MASTER      ?= $(DEPS)/cc-master
SLAVE       ?= $(DEPS)/cc-slave/src
MASTER_REPO  = https://github.com/mod-audio/cc-master.git
SLAVE_REPO   = https://github.com/mod-audio/cc-slave.git
MASTER_REV   = 4b3bac70e030367094c196f2e73aabc848c8eef3
SLAVE_REV    = 2caa4a9716223e30c2ea23c5a19d1b43b3e78bf5

CFLAGS = -std=gnu99 -O0 -g -Wall -Wno-unused-parameter -I. -I$(SLAVE)

all: check-deps fakebox controlchaind

check-deps:
	@test -d $(SLAVE) -a -d $(MASTER) || { echo "MOD libraries missing: run  make deps  first"; exit 1; }

deps:
	mkdir -p $(DEPS)
	test -d $(DEPS)/cc-master || git clone -q $(MASTER_REPO) $(DEPS)/cc-master
	test -d $(DEPS)/cc-slave  || git clone -q $(SLAVE_REPO)  $(DEPS)/cc-slave
	git -C $(DEPS)/cc-master checkout -q $(MASTER_REV)
	git -C $(DEPS)/cc-slave  checkout -q $(SLAVE_REV)
	@echo "deps ready: cc-master $(MASTER_REV), cc-slave $(SLAVE_REV)"

fakebox: fakebox.c config.h $(wildcard $(SLAVE)/*.c)
	$(CC) $(CFLAGS) fakebox.c $(SLAVE)/*.c -lm -o $@

# cc-master's bundled waf no longer runs on modern Python, so build directly.
# spshim.c replaces libserialport so the master can open the emulator's virtual ports.
# portsem.h swaps in a semaphore macOS supports (forced on Linux too, so it's tested).
controlchaind: spshim.c portsem.h
	mkdir -p ccm-build
	printf '#define SERVER_NAME "controlchaind"\n#define SERVER_VERSION "0.7.0"\n' > ccm-build/config.h
	# macOS getopt stops at the port name, so "-f" after it was ignored and the
	# server silently daemonized. Start option parsing after the port instead.
	sed 's/^    int opt;$$/    int opt; optind = 2;/' $(MASTER)/server/src/main.c > ccm-build/main.c
	grep -q 'optind = 2;' ccm-build/main.c
	# macOS sockaddr_un has an extra sun_len byte; cc-master's length maths
	# cut the last character off the socket path ("/tmp/control-chain.soc").
	sed -e 's/struct sockaddr_un local;/struct sockaddr_un local; memset(\&local, 0, sizeof local);/' \
	    -e 's/int len = strlen(local.sun_path) + sizeof(local.sun_family);/int len = sizeof(local);/' \
	    $(MASTER)/server/src/sockser.c > ccm-build/sockser.c
	grep -q 'int len = sizeof(local);' ccm-build/sockser.c
	$(CC) -std=gnu99 -O0 -g -DDEBUG -w -include portsem.h -Iccm-build -I$(MASTER)/lib/src -I$(MASTER)/server/src \
	  $(MASTER)/lib/src/*.c $(filter-out %/main.c %/sockser.c,$(wildcard $(MASTER)/server/src/*.c)) ccm-build/main.c ccm-build/sockser.c spshim.c \
	  $$(pkg-config --cflags libserialport) $$(pkg-config --cflags --libs jansson) -lpthread -o $@

clean:
	rm -rf fakebox controlchaind ccm-build

.PHONY: all check-deps deps clean
