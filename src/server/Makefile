watch:
	python src/main.py

shell:
	nix develop

.PHONY: nix-%
nix-%:
	nix develop\
		--command $(MAKE) $*

