# Makefile of FunkLoad xmlrpc demo
.PHONY: clean all start stop restart status
.PHONY:	test credential_test bench credential_bench
.PHONY:	start_monitor stop_monitor restart_monitor
.PHONY:	start_credential stop_credential restart_credential

MONCTL := fl-monitor-ctl monitor.conf
CREDCTL := fl-credential-ctl credential.conf

ifdef URL
# FunkLoad options
	FLOPS = -u $(URL)
else
	FLOPS =
endif

all: test

# testing
test:
	fl-run-test  test_SeamBooking.py -v $(FLOPS)

debug:
	fl-run-test -d test_SeamBooking.py -v $(FLOPS)

# to display donwload of links
debug_verbose:
	fl-run-test -d --debug-level=2 test_SeamBooking.py -v $(FLOPS)

# Render each fetched page in a runing firefox
debug_firefox:
	fl-run-test -dV test_SeamBooking.py -v $(FLOPS)

# benching
bench:
	@$(MONCTL) restart
	-fl-run-bench -c 1:20:40:60 -D 30 -m.01 -M2 test_SeamBooking.py SeamBooking.test_seam_booking $(FLOPS)
	-fl-build-report credential-bench.xml --html
	@$(MONCTL) stop


# misc
start_monitor:
	$(MONCTL) start

stop_monitor:
	-$(MONCTL) stop

restart_monitor:
	$(MONCTL) restart

status:
	$(MONCTL) status;

stop: stop_monitor

start: start_monitor

restart: restart_monitor

clean:
	-find . "(" -name "*~" -or  -name ".#*" ")" -print0 | xargs -0 rm -f
