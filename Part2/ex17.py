# TODO: Refer to the objective and sample output and figure out your own code!
# Time to graduate :p
import random

print("What's your name?")
name = input()

adjective = ["Joyful ", "Intuitive ", "Wistful ", "Mischievious ", "Annoying ", "Passionate "]
animals = ["Beaver", "Meerkat", "Ladybug", "Dragon", "Toad", "Mantis"]

res1 = random.choice(adjective)
res2 = random.choice(animals)
codename = res1 + res2
lucky_number = random.randint(1, 99)

print(f"{name}, your codename is: {codename}")
print(f"Your lucky number is: {lucky_number}")