import shelve


player_classes = ["Warrior", "Rogue", "Hunter", "Warlock", "Mage", "Priest",
                  "Shaman", "Druid"]

# Apufunktio oikean eventin valitsemista varte.
def selectevent(raidname):
    setup_shelf = None

    if raidname == "MC":
        setup_shelf = shelve.open("MC", writeback=True)

    elif raidname == "BWL":
        setup_shelf = shelve.open("BWL", writeback=True)

    return setup_shelf


def is_valid_class(name):
    name = name.title()

    if name in player_classes:
        return True, name
    else:
        return False, name
