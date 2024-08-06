watch:
	python src/main.py

shell:
	nix develop

format:
	black src

.PHONY: nix-%
nix-%:
	nix develop\
		--command $(MAKE) $*

