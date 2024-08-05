run_api:
	make -C ./src/api run

run_server:
	make -C ./src/server nix-watch

run_client:
	make -C ./src/client nix-start
