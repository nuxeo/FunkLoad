# FunkLoad test configuration file
# $Id: $

# ------------------------------------------------------------
# Main section
#
[main]
title=%(class_name)s
description=XXX the TestCase class description
# the server url to test
url=%(server_url)s
# the User-Agent header to send
#user_agent = Mozilla/5.0 Firefox/1.0.6


# ------------------------------------------------------------
# Tests description and configuration
#
[test_%(test_name)s]
description=XXX the test case description


# ------------------------------------------------------------
# Credential access
#
[credential]
host=localhost
port=8007


# ------------------------------------------------------------
# Monitoring configuration
#
[monitor]
#hosts=localhost

# Each host in [monitor]hosts should have a section
# with a 'port' and 'description' keys
[localhost]
port=8008
description=The benching machine


# ------------------------------------------------------------
# Configuration for unit test mode fl-run-test
#
[ftest]

# log_to destination =
# console - to the screen
# file - to a file
log_to = console file

# log_path = path and file name to store log file
log_path = %(test_name)s-test.log

# result_path = path to store the xml result file
result_path = %(test_name)s-test.xml

# expect_codes = list of successfull HTTP response code
expect_codes =  200:301:302

# sleeptime_min = minimum amount of time in seconds to sleep between requests
#                 to the host
sleep_time_min = 0

# sleeptime_max = maximum amount of time in seconds to sleep between requests
#                 to the host
sleep_time_max = 0


# ------------------------------------------------------------
# Configuration for bench mode fl-run-bench
#
[bench]

# cycles = list of cycles with their number of concurrent users
cycles =  1:2:3

# duration = duration of a cycle in seconds
duration = 30

# startup_delay = time to wait between starting-up threads in seconds
startup_delay = 0.2

# sleep_time = time to wait between test in seconds
sleep_time = 1

# cycle_time = time to wait between cycle in seconds
cycle_time = 1

# same keys than in [ftest] section
log_to = file
log_path = %(test_name)s-bench.log
result_path = %(test_name)s-bench.xml
expect_codes =  200:301:302
sleep_time_min = 0
sleep_time_max = 2
