watch:
	python src/main.py

.PHONY: nix-%
nix-%:
	nix develop $(NIX_OPTIONS)\
		--command $(MAKE) $*

