import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent))

"""
Defines the standard questions for each PII type to be used by the 
QaPiiDetector.

Each PII type is mapped to a list of questions. The detector will iterate
through these questions to find the corresponding PII.
"""

PII_QUESTIONS = {
    "PERSON": [
        "What is the person's name?",
        "Who is the individual mentioned?"
    ],
    "DATE": [
        "What is the date?",
        "What is the date mentioned?"
    ],
    "LOCATION": [
        "What is the address?",
        "What is the location mentioned?",
        "Where is the place mentioned?"
    ],
    "EMAIL_ADDRESS": [
        "What is the email address?"
    ],
    "PHONE_NUMBER": [
        "What is the phone number?",
        "What is the contact number?"
    ],
    "CREDIT_CARD": [
        "What is the credit card number?"
    ],
    "SSN": [
        "What is the Social Security Number?",
    ],
    "DRIVERS_LICENSE": [
        "What is the driver's license number?"
    ],
    "API_KEY": [
        "What is the API key?",
        "What is the token?",
        "What is the secret key?",
        "What is the access key?"
    ],
    "DATABASE_URL": [
        "What is the database URL?",
        "What is the database connection string?"
    ],
    "IP_ADDRESS": [
        "What is the IP address?",
        "What is the IP address mentioned?"
    ]
}
