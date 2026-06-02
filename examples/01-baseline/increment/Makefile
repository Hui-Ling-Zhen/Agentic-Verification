# Increment — Adder 增量验证

ROOT := ../..
BASELINE_OUT := ../output
INC_CONFIG := $(ROOT)/examples/01-baseline/workflow/inc.yaml

VERIAGENT_PY := $(wildcard $(ROOT)/veriagent.py)
ifdef VERIAGENT_PY
CMD ?= python3 $(ROOT)/veriagent.py
else
CMD ?= veriagent
endif

CONT ?= false

.PHONY: init init_test diff help

help:
	@echo "Prerequisite: run 'make quick' or 'make baseline' in 01-baseline/ first."
	@echo "Targets: init (supervised Codex), diff (apply RTL changes)"

init_workspace:
	@if [ ! -d $(BASELINE_OUT)/workspace_Adder ]; then \
		echo "Error: Baseline not found at $(BASELINE_OUT)/workspace_Adder"; \
		echo "Run: cd .. && make quick"; \
		exit 1; \
	fi
	@if [ $(CONT) = false ]; then \
		echo "Refreshing increment/output from baseline..."; \
		rm -rf output; \
		cp -r $(BASELINE_OUT) output; \
		rm -f output/workspace_Adder/.veriagent 2>/dev/null || true; \
	fi

init: init_workspace
	$(CMD) output/workspace_Adder/ Adder --config $(INC_CONFIG) \
		--mcp-server-no-file-tools -s -hm --tui --loop --backend=codex \
		--no-embed-tools $(ARGS)

diff:
	rm -rf output/workspace_Adder/Adder || true
	cat Adder_new.v > output/workspace_Adder/Adder_RTL/Adder.v
	picker export output/workspace_Adder/Adder_RTL/Adder.v --rw 1 --sname Adder --tdir output/workspace_Adder/ -c -w output/workspace_Adder/Adder/Adder.fst
	cp Adder_new_README.md output/workspace_Adder/Adder/README.md || true
