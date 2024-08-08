CONTAINER_ENGINE := $(shell if command -v podman &> /dev/null; then echo podman; else echo docker; fi)

run:
	$(CONTAINER_ENGINE) run --rm -ti --name local-ai -v $(CURDIR)/models:/build/models -p 8080:8080 localai/localai:latest-aio-cpu
