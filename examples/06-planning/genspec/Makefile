# Makefile for GenSpec example

# First try ../../veriagent.py then fallback to system installed veriagent
VERIAGENT_PY := $(wildcard ../../../veriagent.py)
REPO_ROOT := ../../..
VERIAGENT_SUPERVISED_CODEX := $(shell PYTHONPATH=$(abspath $(REPO_ROOT)) python3 -c "from veriagent.runtime_contract import official_launch_args_string; print(official_launch_args_string())")

ifdef VERIAGENT_PY
CMD ?= python3 ../../../veriagent.py
else
CMD ?= veriagent
endif

clean:
	rm ./output -rf

init_%: clean
	mkdir output
	cp -r $* output/

spec_%:
	$(CMD) output/ $* --config ../workflow/genspec.yaml --guid-doc-path ./SpecDoc/dut_spec_template.md \
		$(VERIAGENT_SUPERVISED_CODEX) --no-embed-tools $(ARGS)

spec_mcp_%: spec_%
