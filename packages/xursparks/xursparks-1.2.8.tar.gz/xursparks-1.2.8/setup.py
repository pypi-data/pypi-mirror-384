from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")
	
version = '1.2.8'

setup(
    name='xursparks',
    version=version,
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=install_requires,
    author='Randell Gabriel Santos',
    author_email='randellsantos@gmail.com',
    description='Encapsulating Apache Spark for Easy Usage',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/dev-doods687/xursparks',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
