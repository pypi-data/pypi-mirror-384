from setuptools import setup, find_packages

setup(
	name='importer',
	version='1.0.0',
	packages=find_packages(),
	install_requires=['tqdm'],
	description='A library related to Python models and files',
	long_description=open('README.md', encoding='utf-8').read(),
	long_description_content_type='text/markdown',
	author='Moamen Waleed',
	url='https://github.com/mikl37228-spec/importer',
	license='MIT',
	python_requires='>=3.7',
)
