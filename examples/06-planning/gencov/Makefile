# Makefile for Gencov example

# First try ../../veriagent.py then fallback to system installed veriagent
VERIAGENT_PY := $(wildcard ../../../veriagent.py)
REPO_ROOT := ../../..
VERIAGENT_SUPERVISED_CODEX := $(shell PYTHONPATH=$(abspath $(REPO_ROOT)) python3 -c "from veriagent.runtime_contract import official_launch_args_string; print(official_launch_args_string())")

ifdef VERIAGENT_PY
CMD ?= python3 ../../../veriagent.py
else
CMD ?= veriagent
endif

# Output directory (project root by default)
OUT_DIR ?= ../../../output
OUT_DIR_ABS := $(abspath $(OUT_DIR))

clean:
	rm -rf $(OUT_DIR_ABS)

init_%: clean
	mkdir -p $(OUT_DIR_ABS)
	cp -r $* $(OUT_DIR_ABS)/
	cp -r ../../../veriagent/lang/zh/doc/Guide_Doc $(OUT_DIR_ABS)/
	mkdir -p $(OUT_DIR_ABS)/$*/gencov/skeletons
	cp -r GenCov/skeletons/* $(OUT_DIR_ABS)/$*/gencov/skeletons/
	cp GenCov/check_tp_consistency.py $(OUT_DIR_ABS)/$*/gencov/
	@hvp_src=$$(ls $*/spec/*.hvp $*/hvp/*.hvp 2>/dev/null | head -n 1); \
	if [ -n "$$hvp_src" ]; then \
		mkdir -p $(OUT_DIR_ABS)/$*/spec; \
		cp -f "$$hvp_src" "$(OUT_DIR_ABS)/$*/spec/$*_verification_plan.hvp"; \
	else \
		echo "WARNING: no .hvp found under $*/spec or $*/hvp"; \
	fi

gencov_%:
	$(CMD) $(OUT_DIR_ABS)/ $* --config ../workflow/gencov.yaml \
		$(VERIAGENT_SUPERVISED_CODEX) --no-embed-tools $(ARGS)

gencov_mcp_%: gencov_%
