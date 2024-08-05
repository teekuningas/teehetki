start:
	npm start

.PHONY: nix-%
nix-%:
		nix develop $(NIX_OPTIONS)\
			--command $(MAKE) $*

