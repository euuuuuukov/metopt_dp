START_ZB1, START_ZB2, START_DEP = 100, 800, 400

START_FREE = 600

CHANGE_ZB1, CHANGE_ZB2, CHANGE_DEP = 25, 200, 100

MIN_ZB1, MIN_ZB2, MIN_DEP = 30, 150, 100

COMMISSION_ZB1, COMMISSION_ZB2, COMMISSION_DEP = 0.04, 0.07, 0.05

STAGES = {
    1: {
        1: {
            'p': 0.6, 'zb1': 1.2, 'zb2': 1.1, 'dep': 1.07
        },
        0: {
            'p': 0.3, 'zb1': 1.05, 'zb2': 1.02, 'dep': 1.03
        },
        -1: {
            'p': 0.1, 'zb1': 0.8, 'zb2': 0.95, 'dep': 1
        }
    },
    2: {
        1: {
            'p': 0.3, 'zb1': 1.4, 'zb2': 1.15, 'dep': 1.01
        },
        0: {
            'p': 0.2, 'zb1': 1.05, 'zb2': 1, 'dep': 1
        },
        -1: {
            'p': 0.5, 'zb1': 0.6, 'zb2': 0.9, 'dep': 1
        }
    },
    3: {
        1: {
            'p': 0.4, 'zb1': 1.15, 'zb2': 1.12, 'dep': 1.05
        },
        0: {
            'p': 0.4, 'zb1': 1.05, 'zb2': 1.01, 'dep': 1.01
        },
        -1: {
            'p': 0.2, 'zb1': 0.7, 'zb2': 0.94, 'dep': 1
        }
    },
}
