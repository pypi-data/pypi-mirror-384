import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(name='rheia_meca2675',
      version='1.1.15',
      description='Robust design optimization of renewable Hydrogen and dErIved energy cArrier systems',
      url='https://github.com/rheia-framework/RHEIA',
      author='Diederik Coppitters, Panagiotis Tsirikoglou, Ward De Paepe, Konstantinos Kyprianidis, Anestis Kalfas, Francesco Contino',
      author_email='rheia.framework@gmail.com',
      package_dir={"": "src"},
      packages= setuptools.find_packages(where="src"),
      classifiers=[
                "Programming Language :: Python :: 3",
                "License :: OSI Approved :: MIT License",
                "Operating System :: OS Independent",
      ],       
      install_requires=[
      'pyDOE>=0.3.8',
      'deap>=1.3.1',
      'numpy>=1.24.1',
      'scipy>=1.10.0',
      'sobolsequence>=0.2.1',
      'pandas>=1.5.3',
      'matplotlib>=3.2.2',
      'pvlib>=0.9.4',
      'h5py>=3.8.0'
      ],
      python_requires = ">=3.9",
      include_package_data=True,
      zip_safe=False)