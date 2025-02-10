venv:
	python3 -m pip install virtualenv
	python3 -m venv .venv
	source .venv/bin/activate
	python3 -m pip install -r requirements.txt

run:
	python3 -m frontend.main_window
