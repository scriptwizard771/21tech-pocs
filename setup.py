from setuptools import setup, find_packages

setup(
    name="twenty_one_tech_pocs",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "Django==4.2.7",
        "djangorestframework==3.14.0",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "psycopg2-binary==2.9.9",
        "gunicorn==21.2.0",
        "django-cors-headers==4.3.1",
        "pydantic>=2.7.4,<3.0.0",
        "langchain==0.3.8",
        "langchain-core>=0.3.0,<0.4.0",
        "langchain-openai==0.2.9",
        "langchain-community==0.3.8",
    ],
    python_requires=">=3.11",
) 