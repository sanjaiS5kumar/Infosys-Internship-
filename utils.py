import random, string

def generate_pnr():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

