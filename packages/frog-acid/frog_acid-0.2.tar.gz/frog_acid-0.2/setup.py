from setuptools import setup, find_packages

setup(
    name='frog-acid',  # Change this to your new name
    version='0.2',
    description='A 3D engine using PyOpenGL and Pygame',
    author='Pratyush wani',
    author_email='wanipratyush2@gmail.com',
    packages=['pythontwo'],  # Make sure the package name matches your project folder
    install_requires=[
        'pygame',
        'pyopengl'
    ],
    classifiers=[  # Add some classifiers to help users find your package
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',  # Update with your license
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',  # Python version compatibility
    long_description=open("README.md", encoding="utf-8").read(),  # Read long description from README.md
    long_description_content_type='text/markdown',
    url='https://github.com/procutepro/acid',  # URL to your project
    )
