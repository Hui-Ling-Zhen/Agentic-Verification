# Sbuffer — Makefile

ROOT := ../..
.PHONY: run run-with-mock help

help:
	@echo "  run            - standard UT (no Mock stages)"
	@echo "  run-with-mock  - Mock + BBV flagship mode"

run:
	$(MAKE) -C $(ROOT) mcp_Sbuffer $(ARGS)

run-with-mock:
	ENABLE_LLM_FAIL_SUGGESTION=true ENABLE_LLM_PASS_SUGGESTION=true \
	IGNORE_MOCK_COMPONENT=false BBV=true \
	$(MAKE) -C $(ROOT) mcp_Sbuffer $(ARGS)
