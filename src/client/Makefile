start:
	npm start

shell:
	nix develop

.PHONY: nix-%
nix-%:
		nix develop\
			--command $(MAKE) $*

