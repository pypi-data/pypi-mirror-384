# Benchmark commands
BASE_URL ?= https://ifh-core-api-dr-benchmark-048d364b548f5d9790082d8ba4fb44d8.us.langgraph.app
RAMP_START ?= 10
RAMP_END ?= 1000
RAMP_MULTIPLIER ?= 2
WAIT_SECONDS ?= 60
SUCCESS_THRESHOLD ?= 0.99
CLEAR_BETWEEN_STEPS ?= true
CLEAR_DELAY_SECONDS ?= 5
DATA_SIZE ?= 1000
DELAY ?= 0
EXPAND ?= 10
STEPS ?= 10

benchmark-burst:
	make benchmark-reset
	k6 run burst.js

benchmark-ramp:
	make benchmark-reset
	k6 run --out json=raw_data_$(shell date +%Y-%m-%dT%H-%M-%S).json ramp.js

benchmark-capacity:
	rm -f capacity_summary_t*.json capacity_report_*.json capacity_raw_t*.json capacity_hist_*.png capacity_pie_*.png
	npm install
	BASE_URL=$(BASE_URL) \
	RAMP_START=$(RAMP_START) \
	RAMP_END=$(RAMP_END) \
	RAMP_MULTIPLIER=$(RAMP_MULTIPLIER) \
	WAIT_SECONDS=$(WAIT_SECONDS) \
	SUCCESS_THRESHOLD=$(SUCCESS_THRESHOLD) \
	CLEAR_BETWEEN_STEPS=$(CLEAR_BETWEEN_STEPS) \
	CLEAR_DELAY_SECONDS=$(CLEAR_DELAY_SECONDS) \
	DATA_SIZE=$(DATA_SIZE) \
	DELAY=$(DELAY) \
	EXPAND=$(EXPAND) \
	STEPS=$(STEPS) \
	node capacity_runner.mjs

benchmark-charts:
	npm install
	node graphs.js $(shell ls -t raw_data_*.json | head -1) true

benchmark-reset:
	node clean.js

benchmark-new-revision:
	node update-revision.js

benchmark-clean:
	rm -f results_*.json summary_*.json raw_data_*.json *_chart_*.png

benchmark-clean-charts:
	rm -f *_chart_*.png
