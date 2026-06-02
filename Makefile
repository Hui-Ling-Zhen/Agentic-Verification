
# Current Workspace Dir
CWD ?= output/workspace_$*
# Optional workflow override; default is per-DUT storyline workflow (see dut_workflow_cfg)
CFG ?=
BBV ?= false
SRC ?= examples
# Override DUT RTL/spec source directory (see examples/README.md)
DUT_SRC_DIR ?=

# Per-DUT example source paths (reorganized examples/ layout)
DUT_SRC_Adder := examples/01-baseline/adder
DUT_SRC_Mux := examples/01-baseline/mux
DUT_SRC_Sbuffer := examples/03-microarch/Sbuffer
DUT_SRC_IntegerDivider := examples/04-algorithm/integer-divider
DUT_SRC_ALU754 := examples/04-algorithm/ieee754-alu
DUT_SRC_uart_16550 := examples/02-peripheral-ip/uart_16550

# Per-DUT workflow configs (externalized under examples/*/workflow/)
WORKFLOW_CFG_Adder := examples/01-baseline/workflow/default.yaml
WORKFLOW_CFG_Mux := examples/01-baseline/workflow/default.yaml
WORKFLOW_CFG_Sbuffer := examples/03-microarch/workflow/default.yaml
WORKFLOW_CFG_IntegerDivider := examples/04-algorithm/workflow/default.yaml
WORKFLOW_CFG_ALU754 := examples/04-algorithm/workflow/default.yaml
WORKFLOW_CFG_uart_16550 := examples/02-peripheral-ip/workflow/default.yaml

define dut_src_dir
$(if $(DUT_SRC_$1),$(DUT_SRC_$1),$(SRC)/$1)
endef

define dut_workflow_cfg
$(if $(WORKFLOW_CFG_$1),$(WORKFLOW_CFG_$1),examples/01-baseline/workflow/default.yaml)
endef

define resolve_workflow_cfg
$(if $(CFG),$(CFG),$(call dut_workflow_cfg,$1))
endef

# Supervised Codex: VeriAgent runtime (MCP + loop + stage/checker) + Codex cognition (CmdLineBackend)
VERIAGENT_SUPERVISED_CODEX := --mcp-server-no-file-tools -s -hm --tui --loop --backend=codex
SWARM_IMAGE ?= ghcr.nju.edu.cn/xs-mlvp/veriagent:latest
SWARM_NETWORK ?= veriagent_net
SWARM_MASTER_SERVICE ?= veriagent_master
SWARM_MASTER_PORT ?= 8800
SWARM_MASTER_PERSIST ?= /tmp/veriagent_master
SWARM_DOCKER_SOCK ?= /var/run/docker.sock
SWARM_LOCAL_VERIAGENT_DIR := $(CURDIR)
MASTER_IP ?= 127.0.0.1

ifneq ($(strip $(VERIAGENT_MASTER_SOURCE)),)
SWARM_MASTER_SOURCE_DIR := $(abspath $(VERIAGENT_MASTER_SOURCE))
SWARM_MASTER_VERIAGENT_MOUNT := --mount type=bind,source=$(SWARM_MASTER_SOURCE_DIR),target=/VeriAgent
SWARM_MASTER_CMD := python3 /VeriAgent/veriagent/cli.py
SWARM_MASTER_SOURCE_ENV := --env VERIAGENT_MASTER_SOURCE=$(SWARM_MASTER_SOURCE_DIR)
else
SWARM_MASTER_SOURCE_DIR :=
SWARM_MASTER_VERIAGENT_MOUNT :=
SWARM_MASTER_CMD := veriagent
SWARM_MASTER_SOURCE_ENV := --env VERIAGENT_MASTER_SOURCE=
endif

VERIAGENT_PY := $(wildcard veriagent.py)
ifdef VERIAGENT_PY
CMD ?= python3 veriagent.py
else
CMD ?= veriagent
endif

all: clean test

init:
	pip3 install -r requirements.txt

reset_%:
	rm $(CWD)/unity_test -rf  || true
	rm $(CWD)/.veriagent -rf  || true
	rm $(CWD)/uc_test_report -rf  || true
	rm $(CWD)/*.md -rf  || true

init_%:
	@DUT_SRC="$(if $(DUT_SRC_DIR),$(DUT_SRC_DIR),$(call dut_src_dir,$*))"; \
	if [ ! -d "$$DUT_SRC" ]; then \
		echo "Error: DUT source not found: $$DUT_SRC"; \
		exit 1; \
	fi; \
	mkdir -p $(CWD)/$*_RTL; \
	cp $$DUT_SRC/*.v $(CWD)/$*_RTL/ 2>/dev/null || true; \
	cp $$DUT_SRC/*.sv $(CWD)/$*_RTL/ 2>/dev/null || true; \
	cp $$DUT_SRC/*.vh $(CWD)/$*_RTL/ 2>/dev/null || true; \
	cp $$DUT_SRC/*.scala $(CWD)/$*_RTL/ 2>/dev/null || true; \
	cp $$DUT_SRC/filelist.txt $(CWD)/$*_RTL/ 2>/dev/null || true
	@if [ ! -d $(CWD)/$* ]; then \
		option_fs=""; \
		if [ -f $(CWD)/$*_RTL/filelist.txt ]; then \
			option_fs="--fs $(CWD)/$*_RTL/filelist.txt"; \
		fi; \
		if [ -f $(CWD)/$*_RTL/$*.v ]; then \
			picker export $(CWD)/$*_RTL/$*.v --rw 1 --sname $* --tdir $(CWD)/ -c -w $(CWD)/$*/$*.fst $$option_fs; \
		elif [ -f $(CWD)/$*_RTL/$*.sv ]; then \
			picker export $(CWD)/$*_RTL/$*.sv --rw 1 --sname $* --tdir $(CWD)/ -c -w $(CWD)/$*/$*.fst $$option_fs; \
		fi; \
	fi
	@DUT_SRC="$(if $(DUT_SRC_DIR),$(DUT_SRC_DIR),$(call dut_src_dir,$*))"; \
	cp $$DUT_SRC/*.md $(CWD)/$*/ 2>/dev/null || true; \
	cp $$DUT_SRC/*.py $(CWD)/$*/ 2>/dev/null || true; \
	rm -rf $(CWD)/skills 2>/dev/null || true; \
	if [ -d "$$DUT_SRC/skills" ]; then \
		cp -r "$$DUT_SRC/skills" $(CWD)/skills; \
	elif [ -d "$$(dirname $$DUT_SRC)/skills" ]; then \
		cp -r "$$(dirname $$DUT_SRC)/skills" $(CWD)/skills; \
	fi
	@if [ $(BBV) = "true" ]; then \
		echo "Enable BBV mode: clear RTL files"; \
		for f in $(CWD)/$*/$*.v $(CWD)/$*/$*.sv $(CWD)/$*/$*.vh; do \
			if [ -f $$f ]; then \
				echo "clear file $$f"; \
				echo "" > $$f; \
			fi; \
		done; \
		for f in `find $(CWD)/$*_RTL/*|grep -v '.scala'`; do \
			echo "" > $$f; \
		done; \
	fi
	@python3 $(CWD)/$*/example.py || { echo "Error: picker try to generate DUT, but failed.\n"; exit 1; }

test_%: init_%
	$(CMD) $(CWD)/ $* --config $(call resolve_workflow_cfg,$*) $(VERIAGENT_SUPERVISED_CODEX) ${ARGS}

test_with_master_%: init_%
	$(CMD) $(CWD)/ $* --config $(call resolve_workflow_cfg,$*) $(VERIAGENT_SUPERVISED_CODEX) --master ${MASTER_IP} --export-cmd-api ${ARGS}

mcp_%: init_%
	$(CMD) $(CWD)/ $* --config $(call resolve_workflow_cfg,$*) $(VERIAGENT_SUPERVISED_CODEX) ${ARGS}

mcp_with_master_%: init_%
	$(CMD) $(CWD)/ $* --config $(call resolve_workflow_cfg,$*) $(VERIAGENT_SUPERVISED_CODEX) --master ${MASTER_IP} --export-cmd-api ${ARGS}

# Alias: same as mcp_% (supervised Codex only)
mcp_all_tools_%:
	@$(MAKE) mcp_$* $(ARGS)

clean_%:
	rm -rf $(CWD)

clean:
	rm -rf .pytest_cache
	rm -rf VeriAgent.egg-info
	rm -rf build
	rm -rf dist
	find ./ -name '*.dat'|xargs rm -f
	find ./ -name '*.vcd'|xargs rm -f
	find ./ -name '*.fst'|xargs rm -f
	find ./ -name __pycache__|xargs rm -rf
	find ./ -name output|xargs rm -rf

clean_test_%:
	rm -rf $(CWD)/unity_test

continue_%:
	$(CMD) $(CWD)/ $* --config $(call resolve_workflow_cfg,$*) $(VERIAGENT_SUPERVISED_CODEX) ${ARGS}

as_master:
	$(CMD) --as-master ${ARGS}

as_master_persist:
	$(CMD) --as-master-persist ${PATH_PERSISTENT} --as-master ${ARGS}

swarm_check:
	@command -v docker >/dev/null 2>&1 || { echo "Error: docker CLI is not installed or not in PATH."; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "Error: Docker daemon is not available. Please start Docker first."; exit 1; }
	@test -S $(SWARM_DOCKER_SOCK) || { echo "Error: Docker socket $(SWARM_DOCKER_SOCK) is not available."; exit 1; }
	@if [ -n "$(SWARM_MASTER_SOURCE_DIR)" ] && [ ! -f "$(SWARM_MASTER_SOURCE_DIR)/veriagent/cli.py" ]; then \
		echo "Error: VERIAGENT_MASTER_SOURCE must point to a VeriAgent source tree containing veriagent/cli.py: $(SWARM_MASTER_SOURCE_DIR)"; \
		exit 1; \
	fi
	@state=$$(docker info --format '{{.Swarm.LocalNodeState}}' 2>/dev/null); \
	if [ "$$state" != "active" ]; then \
		echo "Error: Docker Swarm is not active (state: $${state:-unknown})."; \
		echo "Hint: initialize or join a swarm first, for example: docker swarm init"; \
		exit 1; \
	fi
	@control=$$(docker info --format '{{.Swarm.ControlAvailable}}' 2>/dev/null); \
	if [ "$$control" != "true" ]; then \
		echo "Error: this Docker node is not a Swarm manager, so it cannot launch Swarm services."; \
		echo "Hint: run make swarm_master on a manager node, or promote this node with: docker node promote <node>"; \
		exit 1; \
	fi

swarm_init:
	$(MAKE) swarm_check
	@if docker network inspect $(SWARM_NETWORK) >/dev/null 2>&1; then \
		driver=$$(docker network inspect $(SWARM_NETWORK) --format '{{.Driver}}'); \
		scope=$$(docker network inspect $(SWARM_NETWORK) --format '{{.Scope}}'); \
		if [ "$$driver" != "overlay" ] || [ "$$scope" != "swarm" ]; then \
			echo "Error: Docker network $(SWARM_NETWORK) exists but is $$driver/$$scope, expected overlay/swarm."; \
			echo "Hint: remove or rename the existing network, then run make swarm_master again."; \
			exit 1; \
		fi; \
	else \
		docker network create --driver overlay --attachable $(SWARM_NETWORK); \
	fi
	docker image inspect $(SWARM_IMAGE) 1>/dev/null

swarm_clean:
	@echo "Removing existing Docker Swarm services with name prefix $(SWARM_MASTER_SERVICE)...";
	@sid=`docker service list|grep veriagent|awk '{print $$1}'|xargs`; if [ -n "$$sid" ]; then echo "stop service $$sid"; docker service rm $$sid; fi;
	@docker service ls
	@echo "Stop all containers...";
	@did=`docker ps|grep veriagent|awk '{print $$1}'|xargs`; if [ -n "$$did" ]; then echo "stop container $$did"; docker stop $$did; fi;
	@docker ps -a

swarm_master: swarm_init
	@mkdir -p $(SWARM_MASTER_PERSIST)
	@if docker service inspect $(SWARM_MASTER_SERVICE) >/dev/null 2>&1; then \
		echo "Removing existing Docker Swarm service $(SWARM_MASTER_SERVICE)..."; \
		docker service rm $(SWARM_MASTER_SERVICE) >/dev/null; \
		while docker service inspect $(SWARM_MASTER_SERVICE) >/dev/null 2>&1; do sleep 1; done; \
	fi
	docker service create \
		--name $(SWARM_MASTER_SERVICE) \
		--hostname $(SWARM_MASTER_SERVICE) \
		--detach=true \
		--replicas 1 \
		--restart-condition any \
		--constraint node.role==manager \
		--network $(SWARM_NETWORK) \
		--env DOCKER_HOST=unix://$(SWARM_DOCKER_SOCK) \
		--env OPENAI_MODEL=$(OPENAI_MODEL) \
		--env OPENAI_API_KEY=$(OPENAI_API_KEY) \
		--env OPENAI_API_BASE=$(OPENAI_API_BASE) \
		$(SWARM_MASTER_SOURCE_ENV) \
		--publish published=$(SWARM_MASTER_PORT),target=$(SWARM_MASTER_PORT) \
		--mount type=bind,source=$(abspath $(SWARM_MASTER_PERSIST)),target=$(SWARM_MASTER_PERSIST) \
		--mount type=bind,source=$(SWARM_DOCKER_SOCK),target=$(SWARM_DOCKER_SOCK) \
		$(SWARM_MASTER_VERIAGENT_MOUNT) \
		--workdir /workspace/VeriAgent \
		$(SWARM_IMAGE) \
		sh -c "tail -f /dev/null | $(SWARM_MASTER_CMD) --as-master-persist $(SWARM_MASTER_PERSIST) --as-master 0.0.0.0:$(SWARM_MASTER_PORT) --override launch.default_args.launch_mode=docker_swarm $(ARGS)"
	@echo "Waiting for $(SWARM_MASTER_SERVICE) to start..."
	@for i in $$(seq 1 30); do \
		replicas=$$(docker service ls --filter name=$(SWARM_MASTER_SERVICE) --format '{{.Replicas}}' | head -n 1); \
		if [ "$$replicas" = "1/1" ]; then \
			echo "Docker Swarm master is running: http://$(SWARM_MASTER_SERVICE):$(SWARM_MASTER_PORT) on network $(SWARM_NETWORK)"; \
			echo "Published on host: http://127.0.0.1:$(SWARM_MASTER_PORT)"; \
			exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "Error: Docker Swarm service $(SWARM_MASTER_SERVICE) did not reach 1/1 replicas."; \
	echo "Hint: inspect it with: docker service ps $(SWARM_MASTER_SERVICE) --no-trunc"; \
	echo "Hint: view logs with: docker service logs $(SWARM_MASTER_SERVICE)"; \
	exit 1

# Include docs Makefile
-include docs/Makefile

# ---------- Semantic example targets (see examples/README.md) ----------
.PHONY: example-baseline example-bug example-increment example-formal example-flagship example-peripheral example-algorithm

example-baseline:
	$(MAKE) -C examples/01-baseline quick $(ARGS)

example-bug:
	$(MAKE) -C examples/01-baseline bug-hunt $(ARGS)

example-increment:
	$(MAKE) -C examples/01-baseline increment $(ARGS)

example-formal:
	$(MAKE) formal_mcp_arbiter $(ARGS)

example-flagship:
	$(MAKE) -C examples/03-microarch/Sbuffer run-with-mock $(ARGS)

example-peripheral:
	$(MAKE) mcp_uart_16550 $(ARGS)

example-algorithm:
	$(MAKE) mcp_IntegerDivider $(ARGS)

# ---------- Benchmark: aggregate .veriagent/run_manifest.json ----------
.PHONY: benchmark benchmark-clean

benchmark:
	@python3 scripts/benchmark_collect.py --scan output examples

benchmark-clean:
	rm -rf benchmark/summary.csv benchmark/runs.json

# ---------- Formal Verification ----------
FORMAL_DIR   := examples/05-formal
FORMAL_CWD   ?= $(FORMAL_DIR)/output/workspace_$*
FORMAL_CFG   := examples/05-formal/workflow/formal.yaml
FORMAL_DOC   := veriagent/lang/zh/doc/Formal_Doc

formal_init_%:
	mkdir -p $(FORMAL_CWD)
	cp -r $(FORMAL_DIR)/$* $(FORMAL_CWD)/
	rm -rf $(FORMAL_CWD)/skills 2>/dev/null || true
	@if [ -d "$(FORMAL_DIR)/$*/skills" ]; then \
		cp -r $(FORMAL_DIR)/$*/skills $(FORMAL_CWD)/skills; \
	elif [ -d "$(FORMAL_DIR)/skills" ]; then \
		cp -r $(FORMAL_DIR)/skills $(FORMAL_CWD)/skills; \
	fi

formal_%: formal_init_%
	$(CMD) $(FORMAL_CWD)/ $* --config $(FORMAL_CFG) --guid-doc-path $(FORMAL_DOC)/ --output formal_test $(VERIAGENT_SUPERVISED_CODEX) --use-skill $(ARGS)

formal_mcp_%: formal_init_%
	$(CMD) $(FORMAL_CWD)/ $* --config $(FORMAL_CFG) --guid-doc-path $(FORMAL_DOC)/ --output formal_test $(VERIAGENT_SUPERVISED_CODEX) --use-skill --log $(ARGS)

clean_formal:
	rm -rf $(FORMAL_DIR)/output
