
carrier_id = {
    "Foundation Dental": "01",
    "Freedom Spirit": "02",
    "Freedom Platinum": "02",
    "Freedom Spirit Plus": "02",
    "Foundation Vision": "03",
    "Cigna Dental Network Access": "04",
    "Extra Care Package": "05",
    "USA+": "06",
    "USA+ Dental": "06",
    "Safeguard Critical Illness": "07",
    "Ally Rx": "8",
    "Dental Savings": "08",
    "Dental Savings Plus": "08",
    "Sentry Accident Plan": "09"
}

properties = {
    # Foundation Dental
    # https://hiiquote.com/foundation_dental
    '12': {
        "name": "Foundation Dental",
        "plan": {
            'Foundation Dental~~Defender': {
                'description': """
                    Plan Year Deductible (Per Person): $50
                    Plan Year Maximum Benefit (Calendar Year): $1000
                    Deductible Waived In-Network Preventative: Yes
                    Diagnostic & Preventative Services( % of Covered Expenses):  100%
                    Diagnostic & Preventative Services - Benefit Waiting Period: None
                    Basic Services( % of Covered Expenses): 70%
                    Basic Services - Benefit Waiting Period: 6 Months
                    Major Services( % of Covered Expenses): PPO Discount
                    Major Services - Benefit Waiting Period: -
                """
            },
            'Foundation Dental~~Guardian': {
                'description': """
                    Plan Year Deductible (Per Person): $50
                    Plan Year Maximum Benefit (Calendar Year): $500
                    Deductible Waived In-Network Preventative: Yes
                    Diagnostic & Preventative Services( % of Covered Expenses):  100%
                    Diagnostic & Preventative Services - Benefit Waiting Period:  3 Months
                    Basic Services( % of Covered Expenses): 70%
                    Basic Services - Benefit Waiting Period: 6 Months
                    Major Services( % of Covered Expenses): 50%
                    Major Services - Benefit Waiting Period: 12 Months
                """
            },
            'Foundation Dental~~Protector I': {
                'description': """
                    Plan Year Deductible (Per Person): $0
                    Plan Year Maximum Benefit (Calendar Year): $500
                    Deductible Waived In-Network Preventative: Yes
                    Diagnostic & Preventative Services( % of Covered Expenses):  100%
                    Diagnostic & Preventative Services - Benefit Waiting Period:  3 Months
                    Basic Services( % of Covered Expenses): PPO Discount
                    Basic Services - Benefit Waiting Period: -
                    Major Services( % of Covered Expenses): PPO Discount
                    Major Services - Benefit Waiting Period: -
                """
            }
        }
    },


    # Freedom Spirit
    # https://www.hiiquote.com/freedom_spirit
    '16': {
        "name": "Freedom Spirit",
        "plan": {
            'Freedom Spirit~~SPIRIT 100,000': {
                'description': """
                    Principal Sum Amount: $100,000
                    Accidental Loss of Life: 100% of full amt.
                    Accidental Loss of Speech and Loss of Hearing: 100% of full amt.
                    Accidental Loss of Speech and one of Loss of Hand, Loss of Foot, or Loss of Sight in One Eye: 100% of full amt.
                    Accidental Loss of Hearing and one of Loss of Hand, Loss of Foot, or Loss of Sight in One Eye: 100% of full amt.
                    Accidental Loss of Hands (Both), Loss of Feet (Both), Loss of Sight or a combination of any two of Loss of Hand, Loss of Foot, or Loss of Sight of One Eye: 100% of full amt.
                    Accidental Loss of Hand, Loss of Foot, or Loss of Sight of One Eye (Any one of each): 50% of full amt.
                    Accidental Loss of Speech or Loss of Hearing: 50% of full amt.
                    Accidental Loss of Thumb and Index Finger of the same Hand: 25% of full amt.
                """
            },
            'Freedom Spirit~~SPIRIT 50,000': {
                'description': """
                    Principal Sum Amount: $50,000
                    Accidental Loss of Life: 100% of full amt.
                    Accidental Loss of Speech and Loss of Hearing: 100% of full amt.
                    Accidental Loss of Speech and one of Loss of Hand, Loss of Foot, or Loss of Sight in One Eye: 100% of full amt.
                    Accidental Loss of Hearing and one of Loss of Hand, Loss of Foot, or Loss of Sight in One Eye: 100% of full amt.
                    Accidental Loss of Hands (Both), Loss of Feet (Both), Loss of Sight or a combination of any two of Loss of Hand, Loss of Foot, or Loss of Sight of One Eye: 100% of full amt.
                    Accidental Loss of Hand, Loss of Foot, or Loss of Sight of One Eye (Any one of each): 50% of full amt.
                    Accidental Loss of Speech or Loss of Hearing: 50% of full amt.
                    Accidental Loss of Thumb and Index Finger of the same Hand: 25% of full amt.
                """
            }
        }
    },


    # Foundation Vision
    # https://hiiquote.com/foundation_vision.php
    '19': {
        "name": "Foundation Vision",
        "plan": {
            'Foundation Vision~~Foundation Vision': {'description': ''}
        }
    },



    # Cigna Dental Network Access
    # https://www.hiiquote.com/quote/index.php?Plan_ID=51&code=A12304080005
    '20': {
        "name": "Cigna Dental Network Access",
        "plan": {
            'Cigna Dental Network Access~~Cigna Dental @@ Annual': {'description': ''},
            'Cigna Dental Network Access~~Cigna Dental @@ Monthly': {'description': ''},
        }
    },



    # Freedom Spirit
    # https://www.hiiquote.com/freedom_spirit
    '21': {
        "name": "Freedom Spirit Plus",
        'plan': {
            'Freedom Spirit Plus~~100,000': {'description': ''},
            'Freedom Spirit Plus~~50,000': {'description': ''}
        }
    },

    # Freedom Spirit
    # https://www.hiiquote.com/freedom_spiritj
    '26': {
        "name": "Freedom Platinum",
        "plan": {
            'Freedom Spirit Plus~~175,000': {
                'description': ""
            },
            'Freedom Spirit Plus~~125,000': {
                'description': ""
            },
            'Freedom Platinum~~$50,000': {
                'description': ""
            },
            'Freedom Platinum~~$75,000': {
                'description': ""
            }
        }
    },

    # Extra Care Package - 
    # https://hiiquote.com/careington_select
    '28': {
        "name": "Extra Care Package",
        "plan": {
            'Extra Care Package~~ExtraCare': {'description': ''}
        }
    },

    # Safeguard Critical Illness
    # https://www.hiiquote.com/quote/index.php?Plan_ID=88&code=A10230930000016
    '33': {
        "name": "Safeguard Critical Illness",
        "plan": {
            'Safeguard Critical Illness~~$10,000': {'description': ''},
            'Safeguard Critical Illness~~$5,000': {'description': ''},
            'Safeguard Critical Illness~~$7,500': {'description': ''}
        }
    },

    '34': {
        "name": "Dental Savings",
        "plan": {
            'Dental Savings~~Dental': {'description': ''}
        }
    },

    # Savings Plus
    '36': {
        "name": "Dental Savings Plus",
        "plan": {
            'Dental Savings Plus~~Dental': {'description': ''}
        }
    },



    # Sentry Accident Plan
    # https://www.hiiquote.com/quote/index.php?Plan_ID=105&code=A13295000006
    '38': {
        "name": "Sentry Accident Plan",
        "plan": {
            'Sentry Accident Plan~~$1,000': {'description': ''},
            'Sentry Accident Plan~~$10,000': {'description': ''},
            'Sentry Accident Plan~~$15,000': {'description': ''},
            'Sentry Accident Plan~~$20,000': {'description': ''},
            'Sentry Accident Plan~~$3,000': {'description': ''},
            'Sentry Accident Plan~~$5,000': {'description': ''},
            'Sentry Accident Plan~~$500': {'description': ''}
        }
    },

    '40': {
        'name': 'Ally Rx',
        'plan': {
            'Ally Rx~~Ally Rx': {'description': ""},
            'Ally Rx~~Option 2': {'description': ""}
        }
    },

    # USA+ DENTAL
    # https://www.hiiquote.com/quote/index.php?Plan_ID=79&code=A10230930000016
    # USA+ DENTAL id changed from 30 to 48
    '48': {
        "name": "USA+ Dental",
        "plan": {
            'USA+ Dental~~Dental Access': {'description': ""},
            'USA+ Dental~~Dental Care': {'description': ""},
            'USA+ Dental~~Dental Vision Plus': {'description': ""}
        }
    },

}
