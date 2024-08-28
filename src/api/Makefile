CONTAINER_ENGINE := $(shell if command -v podman &> /dev/null; then echo podman; else echo docker; fi)

run:
	$(CONTAINER_ENGINE) run --rm -ti --name local-ai -v $(CURDIR)/models:/build/models -p 8080:8080 localai/localai:latest-aio-cpu

run_custom:
	$(CONTAINER_ENGINE) run --rm -ti --name local-ai -p 8080:8080 -v $(CURDIR)/custom_models:/models quay.io/go-skynet/local-ai:latest-cpu --models-path /models --context-size 1000 --threads 2

