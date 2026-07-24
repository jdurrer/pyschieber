from enum import Enum, auto

## Original implementation
# from pyschieber.suit import Suit
# Trumpf = Enum('Trumpf', ['OBE_ABE', 'UNDE_UFE'] + [str(suit.name) for suit in Suit] + ['SCHIEBEN']) 

# New implementation
class Trumpf(Enum):
    ROSE = auto()
    BELL = auto()
    ACORN = auto()
    SHIELD = auto()
    OBE_ABE = auto()
    UNDE_UFE = auto()
    SCHIEBEN = auto()

def get_trumpf(trumpf: str) -> Trumpf:
    return {
        'OBE_ABE': Trumpf.OBE_ABE,
        'UNDE_UFE': Trumpf.UNDE_UFE,
        'ROSE': Trumpf.ROSE,
        'BELL': Trumpf.BELL,
        'ACORN': Trumpf.ACORN,
        'SHIELD': Trumpf.SHIELD,
    }[trumpf]


def main() -> None:
    print(' ')
    print('This file should not be run by itself.')
    print(' ')
    print('This file explains how Enums work.')
    print(' ')
    print(f'The Enum Trumpf is defined as {Trumpf=}.')
    print(f'Each instance in the Enum is initialized with a name and a unique value. For example for the Trumpf ACORN: {Trumpf.ACORN=}')
    print(f'The name can be gotten by calling {Trumpf.ACORN.name=}.')
    print(f'The value can be gotten by calling {Trumpf.ACORN.value=}.')
    print(' ')
    print('Check functionality:')
    print(get_trumpf('ACORN'))
    

if __name__ == '__main__':
    main()