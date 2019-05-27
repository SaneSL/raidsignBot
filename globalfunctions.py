player_classes = ["Warrior", "Rogue", "Hunter", "Warlock", "Mage", "Priest",
                  "Shaman", "Druid", "Declined"]


def is_valid_class(name):
    name = name.title()

    if name in player_classes:
        return True, name
    else:
        return False, name
