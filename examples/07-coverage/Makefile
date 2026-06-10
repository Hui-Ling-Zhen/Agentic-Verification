# 07-coverage — coverage closure orchestration

ROOT := ../..
OUTPUT_DIR := $(CURDIR)/output

.PHONY: closure mutation-demo help

help:
	@echo "Targets:"
	@echo "  closure - FIFO coverage closure demo"
	@echo "  mutation-demo - Run sandbox mutation/coverage comparison"

closure:
	$(MAKE) -C $(ROOT) mcp_FIFO \
		CWD=$(OUTPUT_DIR)/workspace_FIFO \
		DUT_SRC_DIR=examples/07-coverage/fifo_coverage \
		CFG=examples/07-coverage/workflow/coverage_closure.yaml \
		$(ARGS)

mutation-demo:
	python3 fifo_coverage/run_mutation_demo.py \
		--out-json fifo_coverage/mutation_report.json \
		--out-md fifo_coverage/mutation_report.md
