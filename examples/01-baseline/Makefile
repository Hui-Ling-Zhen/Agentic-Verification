# 01-baseline — Adder / Mux / Increment orchestration

ROOT := ../..
BASELINE_DIR := $(CURDIR)
OUTPUT_DIR := $(BASELINE_DIR)/output
WORKSPACE_ADDER := $(OUTPUT_DIR)/workspace_Adder

.PHONY: quick bug-hunt baseline increment help

help:
	@echo "Targets:"
	@echo "  quick       - Mode A: full UT on Adder (mcp)"
	@echo "  bug-hunt    - Mode B: Mux bug analysis (mcp)"
	@echo "  baseline    - Same as quick; prepares output/ for increment"
	@echo "  increment   - Mode C: incremental verification (see increment/)"

quick baseline:
	$(MAKE) -C $(ROOT) mcp_Adder \
		CWD=$(WORKSPACE_ADDER) \
		DUT_SRC_DIR=examples/01-baseline/adder \
		$(ARGS)

bug-hunt:
	$(MAKE) -C $(ROOT) mcp_Mux \
		CWD=$(OUTPUT_DIR)/workspace_Mux \
		DUT_SRC_DIR=examples/01-baseline/mux \
		$(ARGS)

increment:
	$(MAKE) -C increment $(ARGS)
