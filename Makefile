.PHONY: install uninstall run

install:
	bash scripts/install.sh

uninstall:
	bash scripts/uninstall.sh

run:
	python3 -m tilomenu.menu data/themes/Menu/Vista
