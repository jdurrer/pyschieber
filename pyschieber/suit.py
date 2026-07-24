from enum import Enum, auto

## Original implementation
# Suit = Enum('Suit',['ROSE', 'BELL', 'ACORN', 'SHIELD'])

# New implementation
class Suit(Enum):
    """Represents the four suits used in the game.
    Each suit is a unique enumerated value for card classification and comparison.
    """
    ROSE = auto()
    BELL = auto()
    ACORN = auto()
    SHIELD = auto()


def main() -> None:
    print('This file cannot be run by itself.')
    print(' ')
    print('This file explains how Enums work.')
    print(' ')
    print(f'The Enum Trumpf is defined as {Suit=}.')
    print(f'Each instance in the Enum is initialized with a name and a unique value. For example for the Trumpf ACORN: {Suit.ACORN=}')
    print(f'The name can be gotten by calling {Suit.ACORN=}.')
    print(f'The value can be gotten by calling {Suit.ACORN.value=}.')
    print(type(Suit.ACORN.name))
    
    
if __name__ == '__main__':
    main()