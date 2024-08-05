run_localai:
	podman run --rm -ti --name local-ai -v $(PWD)/models:/build/models -p 8080:8080 localai/localai:latest-aio-cpu

run_server:
	python server/main.py

run_client:
	npm start

shell:
	nix develop

.PHONY: nix-%
nix-%:
	nix develop $(NIX_OPTIONS)\
		--command $(MAKE) $*
