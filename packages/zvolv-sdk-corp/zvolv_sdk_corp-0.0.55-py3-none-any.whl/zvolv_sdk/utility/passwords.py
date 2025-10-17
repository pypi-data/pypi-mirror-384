import hashlib
import string
import random


def password_encrypt_sha512(password):
    """
    Hashes a password using SHA-512.

    :param password: Password to hash (string)
    :return: SHA-512 hash of the password (hexadecimal string).
    """
    return hashlib.sha512(password.encode()).hexdigest()


def generate_random_password(password_length: int = 8, configuration: dict = None, hash_password: bool = False):
    """
    Generate a random password based on given configuration.

    :param password_length: int, The length of the password. Must be at least 8.
    :param configuration: dict, Configuration dictionary specifying the minimum counts for special characters,
                          uppercase letters, digits, and lowercase letters. Example:
                          {
                              "special": {"min": 0, "include": "!@#$%&*"},
                              "upper": {"min": 1},
                              "digits": {"min": 1},
                              "lower": {"min": 1}
                          }
    :param hash_password: bool, If True, returns the SHA-512 hash of the generated password.
    :return: str, Generated password.
    :raises ValueError: If password length is less than 8 or if minimum counts exceed password length.
    """
    if configuration is None:
        configuration = {"special": {"min": 1}, "upper": {"min": 3}, "digits": {"min": 2}}
    if password_length < 8:
        raise ValueError("Password length must be at least 8")

    # Define characters for password
    characters = list(string.ascii_letters + string.digits)
    special_characters = configuration.get("special", {}).get("include", string.punctuation)
    characters += list(special_characters)

    # Shuffle characters to ensure randomness
    random.shuffle(characters)

    password = []

    # Calculate total required length from configuration
    total_min_length = sum(conf["min"] for conf in configuration.values())

    if total_min_length > password_length:
        raise ValueError("Minimum required characters exceed password length")

    while True:
        lower, upper, digits, special = 0, 0, 0, 0

        for _ in range(password_length):
            char = random.choice(characters)
            password.append(char)

            if char.islower():
                lower += 1
            elif char.isupper():
                upper += 1
            elif char.isdigit():
                digits += 1
            elif char in special_characters:
                special += 1

        # Validate generated password
        if (lower >= configuration.get("lower", {}).get("min", 0) and
                upper >= configuration.get("upper", {}).get("min", 0) and
                digits >= configuration.get("digits", {}).get("min", 0) and
                special >= configuration.get("special", {}).get("min", 0)):
            break
        else:
            password.clear()
            random.shuffle(characters)

    # Shuffle the result to ensure randomness
    random.shuffle(password)

    password = "".join(password)

    if hash_password:
        # If hash_password is True, return the SHA-512 hash of the generated password
        return password_encrypt_sha512(password)

    return password
