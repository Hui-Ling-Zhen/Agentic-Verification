# Makefile for GenSpec example

# First try ../../veriagent.py then fallback to system installed veriagent
VERIAGENT_PY := $(wildcard ../../../veriagent.py)

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
	$(CMD) output/ $* --config ./genspec.yaml --guid-doc-path ./SpecDoc/dut_spec_template.md \
		--mcp-server-no-file-tools -s -hm --tui --loop --backend=codex_app_server --no-embed-tools $(ARGS)

spec_mcp_%: spec_%
