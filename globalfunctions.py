import shelve


# Apufunktio oikean eventin valitsemista varte.
def selectevent(raidname):
    setup_shelf = None

    if raidname == "MC":
        setup_shelf = shelve.open("MC", writeback=True)

    elif raidname == "BWL":
        setup_shelf = shelve.open("BWL", writeback=True)

    return setup_shelf
