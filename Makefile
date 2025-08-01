venv:
	python3 -m pip install virtualenv
	python3 -m venv .venv
	source .venv/bin/activate
	python -m pip install -r requirements.txt

database:
	# After making changes to your _old_models, generate a migration script:
	alembic revision --autogenerate -m "V0"
	# Run the migration to update the database schema:
	alembic upgrade head
	# If needed, you can roll back to a previous version:
	alembic downgrade -1

run:
	# Normal startup
	python start.py

	# Rebuild database before starting
	python start.py --rebuild-db

	# Just test config and DB (no frontend/backend launch)
	python start.py --test
