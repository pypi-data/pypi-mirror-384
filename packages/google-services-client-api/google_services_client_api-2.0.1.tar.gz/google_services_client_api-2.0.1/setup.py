from setuptools import setup, find_packages
    
# Lê o arquivo readme.txt
with open('README.md', 'r', encoding='utf-8') as f:
    readme = f.read()

setup(
    name='google_services_client_api',
    version='2.0.1',
    author='DIACDE - TJGO',
    long_description=readme,
    long_description_content_type='text/markdown',
    python_requires='>=3.9.4',
    license='CC BY-NC-SA 4.0',
    packages=find_packages(),
)
