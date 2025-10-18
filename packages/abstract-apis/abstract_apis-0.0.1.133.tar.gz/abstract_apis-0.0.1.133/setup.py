from time import time
import setuptools
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
setuptools.setup(
    name='abstract_apis',
    version='0.0.1.133',
    author='putkoff',
    author_email='partners@abstractendeavors.com',
    description='The `abstract_apis` module is designed to facilitate HTTP requests in Python applications, particularly those that require handling JSON data, dealing with custom API endpoints, and parsing complex nested JSON responses. The module simplifies request handling by abstracting away common tasks such as header management, URL construction, and response parsing.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/AbstractEndeavors/abstract_ide',
    classifiers=[
      'Development Status :: 3 - Alpha',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: MIT License',
      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: 3.11',
    ],
    install_requires=['abstract_utilities','requests'],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
  

)
