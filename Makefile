run:
	@py .\manage.py runserver


migrate:
	@py .\manage.py makemigrations
	@py .\manage.py migrate