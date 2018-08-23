hash= $(shell ./bin/md5_hash.py requirements.txt)
PYTHON_VERSION=3.6
venv = .venv/py${PYTHON_VERSION}-${hash}
dev = $DEVELOMPENT
export DEVELOPMENT=false
default: update_venv

.PHONY: default

${venv}: requirements.txt
	python${PYTHON_VERSION} -m venv ${venv}
	# Install Cython, because it is required to build treap
	. ${venv}/bin/activate; pip install --upgrade pip Cython==0.27 --cache .tmp/
	. ${venv}/bin/activate; pip install -r requirements.txt --cache .tmp/

update_venv: requirements.txt ${venv}
	@rm -f .venv/current
	@ln -s py${PYTHON_VERSION}-$(hash) .venv/current
	@echo Success, to activate the development environment, run:
	@echo "\tsource .venv/current/bin/activate"

install_deps:
	pip install --upgrade --force-reinstall -r requirements.txt
