from colorama import Fore, Style, init

init(autoreset=True)

emoji_map = {
    "A": "🅰️", "B": "🅱️", "C": "🌜", "D": "🌛",
    "E": "🎗️", "F": "🎏", "G": "🌀", "H": "♓",
    "I": "🎐", "J": "🎷", "K": "🎋", "L": "👢",
    "M": "〽️", "N": "🎶", "O": "⭕", "P": "🅿️",
    "Q": "❓", "R": "®️", "S": "💲", "T": "🌴",
    "U": "⛎", "V": "✅", "W": "〰️", "X": "❌",
    "Y": "✌️", "Z": "⚡", " ": "⬜"
}

def fancy_text(text):
    return " ".join([f"{Fore.CYAN}{emoji_map.get(c.upper(), c)}{Style.RESET_ALL}" for c in text])
