# Makefile of FunkLoad xmlrpc demo
.PHONY: clean all start stop restart status
.PHONY:	test credential_test bench credential_bench
.PHONY:	start_monitor stop_monitor restart_monitor
.PHONY:	start_credential stop_credential restart_credential

CREDCTL := fl-credential-ctl cred.conf
MONCTL := fl-monitor-ctl monitor.conf

ifdef URL
# FunkLoad options
	FLOPS = -u $(URL)
else
	FLOPS =
endif

all: test

# testing
test: credential_test

credential_test:
	$(CREDCTL) restart
	fl-run-test test_Credential.py -v $(FLOPS)
	$(CREDCTL) stop

# benching
bench: credential_bench

credential_bench:
	@$(CREDCTL) restart
	@$(MONCTL) restart
	-fl-run-bench -c 1:20:40:60:80:100 -D 10 test_Credential.py Credential.test_credential $(FLOPS)
	-fl-build-report credential-bench.xml --html
	@$(MONCTL) stop
	@$(CREDCTL) stop


# monitor ctl
start_monitor:
	$(MONCTL) start

stop_monitor:
	-$(MONCTL) stop

restart_monitor:
	$(MONCTL) restart

# credential ctl
start_credential:
	$(CREDCTL) start

stop_credential:
	$(CREDCTL) stop

restart_credential:
	$(CREDCTL) restart

# misc
status:
	$(MONCTL) status;
	$(CREDCTL) status;

stop: stop_monitor stop_credential

start: start_monitor start_credential

restart: restart_monitor restart_credential

clean:
	-find . "(" -name "*~" -or  -name ".#*" ")" -print0 | xargs -0 rm -f
