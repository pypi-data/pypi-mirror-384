# freeds
The free data stack CLI and lib.
The project is managed in `poetry` and uses CLI framework `typer`.

There's a freeds packae on pypi, that might work for you, but we're still in alpha here, you'll probably need to fix some bugs to get things running, so better clone the repo.


Get the "python manager" poetry: https://python-poetry.org/

Preferably using pipx: https://github.com/pypa/pipx

Then, ideally, this should work:


    git clone https://github.com/jens-koster/FreeDS.git
    cd freeds
    poetry env use 3.11
    poetry install
    freeds-setup

The setup process is not yet complete and poorly documented.
I'll work on it... but then, Johan, my only user, you've got me on messenger just poke me :-)

oh... I just realised we can have Free Data Stack Haketons.

