from distutils.core import setup


setup(
    name='pyvisual',  # How you named your package folder (MyLib)
    packages=['pyvisual'],  # Chose the same as "name"
    version='0.63',  # Start with a small number and increase it with every change you make
    include_package_data=True,  # Include additional files specified in MANIFEST.in
    package_data={
        'pyvisual': ['assets/*', 'ui/*', 'core/*', 'utils/*'],  # Include the files in assets and ui folders
    },
    license='MIT',  # Chose a license from here: https://help.github.com/articles/licensing-a-repository
    description='A Python GUI Creator for Humans',  # Give a short description about your library
    author='Murtaza Hassan',  # Type in your name
    author_email='contact@murtazahassan.com',  # Type in your E-Mail
    url='https://github.com/user/reponame',  # Provide either the link to your github or to your website
    download_url='https://github.com/user/reponame/archive/v_01.tar.gz',  # I explain this later on
    keywords=['GUI', 'UI', 'Graphical Interface', 'User Interface'],  # Keywords that define your package best
    install_requires=[  # I get to this in a second
        'PySide6',
        'pyqtgraph'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Intended Audience :: Developers',  # Define that your audience are developers
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',  # Again, pick a license
        'Programming Language :: Python :: 3',  # Specify which pyhton versions that you want to support
    ],
    python_requires='>=3.7',  # Supports Python versions 3.7 and above

)
