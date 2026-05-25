# =============================================================================
# Markdown Architecture — Makefile v1.0
# =============================================================================
# Usage:
#   make all                  — run all stages in dependency order
#   make stage-00-intake      — run Stage 00
#   make stage-01-research    — run Stage 01
#   make stage-02-analysis    — run Stage 02
#   make stage-03-output      — run Stage 03
#   make validate             — validate all stage contracts
#   make validate-00          — validate a single stage
#   make audit                — write a PromptExecutionReceipt for Stage 03
#   make clean                — remove non-approved artifacts
#   make help                 — print this message
#
# Parallel validation (fast):
#   make -j$(nproc) validate
# =============================================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

PYTHON         := python3
CONTRACT       := _config/stage-contract.py
AUDIT_LOGGER   := _config/skills/audit_logger.py
OPERATOR       ?= operator

STAGES         := 00-intake 01-research 02-analysis 03-output

# Sentinel files: touched when a stage passes validation.
# Stored in .make/ so they don't pollute stage output dirs.
MAKE_DIR       := .make
SENTINELS      := $(STAGES:%=$(MAKE_DIR)/%.validated)

.PHONY: all validate clean help audit \
	stage-00-intake stage-01-research stage-02-analysis stage-03-output \
	validate-00 validate-01 validate-02 validate-03

# =============================================================================
# Help
# =============================================================================

help:
	@echo ""
	@echo "Markdown Architecture — build targets"
	@echo "--------------------------------------"
	@echo "  make all                run all stages in order"
	@echo "  make stage-00-intake    run Stage 00 (intake)"
	@echo "  make stage-01-research  run Stage 01 (research)"
	@echo "  make stage-02-analysis  run Stage 02 (analysis)"
	@echo "  make stage-03-output    run Stage 03 (output)"
	@echo "  make validate           validate all stage contracts"
	@echo "  make validate-00        validate a single stage (00..03)"
	@echo "  make audit              write PromptExecutionReceipt for Stage 03"
	@echo "  make clean              remove non-approved artifacts"
	@echo ""
	@echo "Parallel validation: make -j\$$(nproc) validate"
	@echo ""

# =============================================================================
# Sentinel directory
# =============================================================================

$(MAKE_DIR):
	@mkdir -p $(MAKE_DIR)

# =============================================================================
# Validate targets (individual)
# =============================================================================

$(MAKE_DIR)/00-intake.validated: $(MAKE_DIR)
	@echo "--- Validating 00-intake ---"
	$(PYTHON) $(CONTRACT) --stage 00-intake
	@touch $@

$(MAKE_DIR)/01-research.validated: $(MAKE_DIR)/00-intake.validated
	@echo "--- Validating 01-research ---"
	$(PYTHON) $(CONTRACT) --stage 01-research
	@touch $@

$(MAKE_DIR)/02-analysis.validated: $(MAKE_DIR)/01-research.validated
	@echo "--- Validating 02-analysis ---"
	$(PYTHON) $(CONTRACT) --stage 02-analysis
	@touch $@

$(MAKE_DIR)/03-output.validated: $(MAKE_DIR)/02-analysis.validated
	@echo "--- Validating 03-output ---"
	$(PYTHON) $(CONTRACT) --stage 03-output
	@touch $@

# Named shorthand targets
validate-00: $(MAKE_DIR)/00-intake.validated
validate-01: $(MAKE_DIR)/01-research.validated
validate-02: $(MAKE_DIR)/02-analysis.validated
validate-03: $(MAKE_DIR)/03-output.validated

# Validate all stages (respects -j for parallelism on independent branches)
validate:
	@echo "=== Validating all stages ==="
	$(PYTHON) $(CONTRACT) --stage all
	@echo "=== All contracts valid ==="

# =============================================================================
# Stage run targets
# (Each target validates its inputs, then runs the stage, then validates output)
# =============================================================================

stage-00-intake: $(MAKE_DIR)
	@echo "=== Stage 00 — Intake ==="
	@echo "Agent: Problem Qualification Agent"
	@echo "Input: raw problem statement"
	@echo "Output: stages/00-intake/output/problem.md"
	@echo ""
	@echo ">> Running intake process..."
	@echo "   (Invoke your agent here, e.g.: claude run --stage 00-intake)"
	@echo ""
	@echo ">> Validating output..."
	$(PYTHON) $(CONTRACT) --stage 00-intake
	@touch $(MAKE_DIR)/00-intake.validated
	@echo "Stage 00 complete."

stage-01-research: $(MAKE_DIR)/00-intake.validated
	@echo "=== Stage 01 — Research ==="
	@echo "Agent: Research & Evidence Agent"
	@echo "Input: stages/00-intake/output/problem.md"
	@echo "Output: brief.md, sources.md, contradictions.md"
	@echo ""
	@echo ">> Running research process..."
	@echo "   (Invoke your agent here, e.g.: claude run --stage 01-research)"
	@echo ""
	@echo ">> Validating output..."
	$(PYTHON) $(CONTRACT) --stage 01-research
	@touch $(MAKE_DIR)/01-research.validated
	@echo "Stage 01 complete."

stage-02-analysis: $(MAKE_DIR)/01-research.validated
	@echo "=== Stage 02 — Analysis ==="
	@echo "Agent: Synthesis & Risk Agent"
	@echo "Input: brief.md, sources.md, contradictions.md"
	@echo "Output: synthesis.md, risk.md"
	@echo ""
	@echo ">> Running analysis process..."
	@echo "   (Invoke your agent here, e.g.: claude run --stage 02-analysis)"
	@echo ""
	@echo ">> Validating output..."
	$(PYTHON) $(CONTRACT) --stage 02-analysis
	@touch $(MAKE_DIR)/02-analysis.validated
	@echo "Stage 02 complete."

stage-03-output: $(MAKE_DIR)/02-analysis.validated
	@echo "=== Stage 03 — Output ==="
	@echo "Agent: Output Assembly Agent"
	@echo "Input: synthesis.md, risk.md, problem.md"
	@echo "Output: <slug>.md, receipts/<timestamp>.json"
	@echo ""
	@echo ">> Running output assembly..."
	@echo "   (Invoke your agent here, e.g.: claude run --stage 03-output)"
	@echo ""
	@echo ">> Writing audit receipt..."
	$(MAKE) audit
	@echo ""
	@echo ">> Validating output..."
	$(PYTHON) $(CONTRACT) --stage 03-output
	@touch $(MAKE_DIR)/03-output.validated
	@echo "Stage 03 complete."

# =============================================================================
# Full pipeline
# =============================================================================

all: stage-00-intake stage-01-research stage-02-analysis stage-03-output
	@echo ""
	@echo "============================="
	@echo "Pipeline complete."
	@echo "============================="

# =============================================================================
# Audit receipt
# =============================================================================

audit:
	@echo ">> Writing PromptExecutionReceipt..."
	$(PYTHON) $(AUDIT_LOGGER) --stage 03-output --operator $(OPERATOR)

# =============================================================================
# Clean
# =============================================================================

clean:
	@echo "Removing non-approved artifacts and sentinel files..."
	@# Remove sentinel cache
	@rm -rf $(MAKE_DIR)
	@# Remove ATTENTION.md flags (resolved by clean)
	@find stages/ -name "ATTENTION.md" -delete 2>/dev/null || true
	@# Remove receipt stubs (not full receipts)
	@find stages/ -path "*/receipts/stub-*.json" -delete 2>/dev/null || true
	@echo "Clean complete. Approved artifacts in output/ dirs are preserved."

# =============================================================================
# Guard: never run make as root
# =============================================================================

ifeq ($(shell id -u), 0)
$(error Do not run make as root.)
endif
