import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime, timedelta
import json
import random
import uuid
from collections import defaultdict
import time
import threading
from matplotlib.patches import Rectangle
import requests
from PIL import Image
import warnings

# Suppress matplotlib font warnings for emojis
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

class MithrilRealtimeDemo:
    def __init__(self, population_size=100, map_bounds=(-122.5, -122.3, 37.7, 37.8), map_filename="map1.png"):
        """
        Initialize Mithril cloaking demonstration with real-time visualization
        population_size: Number of individuals to simulate
        map_bounds: (min_lon, max_lon, min_lat, max_lat) - defaults to SF area
        map_filename: Name of the map file to use as background
        """
        self.population_size = population_size
        self.min_lon, self.max_lon, self.min_lat, self.max_lat = map_bounds
        self.map_filename = map_filename
        
        # Realistic ad tracking services and their ID formats
        self.ad_tracking_services = {
            "LiveRampUI2.0": lambda: f"LR_{random.randint(100000000, 999999999)}",
            "PalantirT&TTag": lambda: f"PLT_{random.randint(10000, 99999)}{random.choice(['A', 'B', 'C', 'D'])}",
            "ExperianEye#": lambda: f"EXP_{random.choice(['US', 'CA', 'UK'])}{random.randint(1000000, 9999999)}",
            "GoogleAdID": lambda: f"GAD_{uuid.uuid4().hex[:16].upper()}",
            "FacebookPixel": lambda: f"FB_{random.randint(1000000000000000, 9999999999999999)}",
            "AmazonDSP": lambda: f"ADSP_{random.choice(['WEST', 'EAST', 'CENT'])}{random.randint(100000, 999999)}",
            "AdobeAudience": lambda: f"AAM_{random.choice(['B2B', 'B2C', 'RTL'])}{random.randint(10000000, 99999999)}",
            "DatabrokerXS": lambda: f"DBX_{random.choice(['PRIME', 'BASIC', 'PRO'])}{random.randint(1000, 9999)}",
            "CriteoConnect": lambda: f"CRT_{random.randint(100000000, 999999999)}{random.choice(['X', 'Y', 'Z'])}",
            "NielsenDAR": lambda: f"NSN_{random.choice(['TV', 'DIG', 'MOB'])}{random.randint(1000000, 9999999)}"
        }
        
        # Realistic first and last names
        self.first_names = [
            "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", 
            "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
            "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Nancy", "Daniel", "Lisa",
            "Matthew", "Betty", "Anthony", "Helen", "Mark", "Sandra", "Donald", "Donna",
            "Steven", "Carol", "Andrew", "Ruth", "Kenneth", "Sharon", "Paul", "Michelle",
            "Joshua", "Laura", "Kevin", "Sarah", "Brian", "Kimberly", "George", "Deborah",
            "Timothy", "Dorothy", "Ronald", "Amy", "Jason", "Angela", "Edward", "Ashley",
            "Jeffrey", "Brenda", "Ryan", "Emma", "Jacob", "Olivia", "Gary", "Cynthia"
        ]
        
        self.last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
            "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
            "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
            "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
            "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
            "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker"
        ]
        
        # Initialize population with unique ad_ids and starting locations
        self.population = []
        self.profiles = defaultdict(list)  # ad_id -> list of location pings
        self.current_chaff_rate = 0.0
        
        # Real-time tracking stats
        self.realtime_stats = {
            'timestamps': [],
            'true_positive_rates': [],
            'false_positive_rates': [],
            'chaff_rates': [],
            'data_points_processed': []
        }
        
        # Animation and plotting setup
        self.fig = None
        self.axes = None
        self.is_running = False
        self.simulation_complete = False
        
        # Live data for location visualization
        self.live_real_locs = {'lons': [], 'lats': []}
        self.live_chaff_locs = {'lons': [], 'lats': []}
        
        # Terminal feed data
        self.terminal_feed = []
        self.max_terminal_lines = 25  # More lines for slower simulation
        
        # Map image
        self.map_image = None
        
        self._initialize_population()
        
    def add_terminal_message(self, message):
        """Add a message to the terminal feed"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.terminal_feed.append(f"[{timestamp}] {message}")
        
        # Keep only the most recent messages
        if len(self.terminal_feed) > self.max_terminal_lines:
            self.terminal_feed = self.terminal_feed[-self.max_terminal_lines:]
    
    def load_map_image(self):
        """Load the map image from S3"""
        try:
            map_url = f'https://mithrilmedia.s3.us-east-1.amazonaws.com/maps/{self.map_filename}'
            response = requests.get(map_url, timeout=10)
            if response.status_code == 200:
                self.map_image = Image.open(requests.get(map_url, stream=True).raw)
                self.add_terminal_message(f"MAP: Loaded {self.map_filename} successfully")
                return True
            else:
                self.add_terminal_message(f"MAP: Failed to load {self.map_filename} (HTTP {response.status_code})")
                return False
        except Exception as e:
            self.add_terminal_message(f"MAP: Error loading {self.map_filename} - {str(e)[:50]}")
            return False
            
    def generate_ip_address(self, person_location='US'):
        """Generate realistic IP addresses based on geographic location"""
        # Common IP ranges for different regions
        ip_ranges = {
            'US_West': ['173.252', '199.201', '208.43', '69.171', '31.13'],
            'US_East': ['54.239', '52.84', '34.196', '107.20', '184.72'],
            'US_Central': ['162.254', '104.16', '198.41', '172.217', '216.58'],
            'ISP_Comcast': ['73.', '96.', '108.', '174.', '98.'],
            'ISP_Verizon': ['71.', '72.', '74.', '75.', '76.'],
            'ISP_ATT': ['99.', '12.', '135.', '192.', '204.'],
            'Mobile_Carrier': ['100.', '10.', '192.168']
        }
        
        # Pick a random range
        range_type = random.choice(list(ip_ranges.keys()))
        prefix = random.choice(ip_ranges[range_type])
        
        # Complete the IP
        if '.' in prefix and len(prefix.split('.')) == 2:
            # Two octets provided
            return f"{prefix}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        else:
            # One octet provided
            return f"{prefix}{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        
    def _initialize_population(self):
        """Create initial population with realistic movement patterns"""
        for i in range(self.population_size):
            # Generate realistic name
            first_name = random.choice(self.first_names)
            last_name = random.choice(self.last_names)
            full_name = f"{first_name} {last_name}"
            
            # Random starting location within bounds
            start_lat = random.uniform(self.min_lat, self.max_lat)
            start_lon = random.uniform(self.min_lon, self.max_lon)
            
            # Generate 2-3 ad tracking identities per person
            num_identities = random.randint(2, 3)
            available_services = list(self.ad_tracking_services.keys())
            selected_services = random.sample(available_services, num_identities)
            
            tracking_identities = []
            for service_name in selected_services:
                ad_id_generator = self.ad_tracking_services[service_name]
                ad_id = ad_id_generator()
                tracking_identities.append({
                    'service': service_name,
                    'ad_id': ad_id
                })
            
            person = {
                'tracking_identities': tracking_identities,
                'primary_service': tracking_identities[0]['service'],  # For backward compatibility
                'primary_ad_id': tracking_identities[0]['ad_id'],     # For backward compatibility
                'name': full_name,
                'first_name': first_name,
                'last_name': last_name,
                'true_lat': start_lat,
                'true_lon': start_lon,
                'base_ip': self.generate_ip_address(),
                'movement_pattern': random.choice(['stationary', 'commuter', 'wanderer']),
                'is_protected': i < 10  # First 10 people are "protected" subjects
            }
            
            self.population.append(person)
            
    def generate_location_ping(self, person, timestamp, is_chaff=False):
        """Generate a location ping JSON for a person"""
        # Pick one of the person's tracking identities randomly
        chosen_identity = random.choice(person['tracking_identities'])
        
        if is_chaff:
            # Chaff locations are completely random within bounds
            lat = random.uniform(self.min_lat, self.max_lat)
            lon = random.uniform(self.min_lon, self.max_lon)
            ad_id = chosen_identity['ad_id']  # Use real ad_id but fake location
            service = chosen_identity['service']
            
            # Generate chaff IP (different from person's real IP)
            ip_address = self.generate_ip_address()
            while ip_address == person['base_ip']:  # Ensure different IP
                ip_address = self.generate_ip_address()
        else:
            # Real location with small movement based on pattern
            movement_size = {
                'stationary': 0.001,   # ~100m
                'commuter': 0.005,     # ~500m  
                'wanderer': 0.01       # ~1km
            }
            
            delta = movement_size[person['movement_pattern']]
            person['true_lat'] += random.uniform(-delta, delta)
            person['true_lon'] += random.uniform(-delta, delta)
            
            # Keep within bounds
            person['true_lat'] = np.clip(person['true_lat'], self.min_lat, self.max_lat)
            person['true_lon'] = np.clip(person['true_lon'], self.min_lon, self.max_lon)
            
            lat, lon = person['true_lat'], person['true_lon']
            ad_id = chosen_identity['ad_id']
            service = chosen_identity['service']
            
            # Real IP with small variation (same ISP/region)
            base_octets = person['base_ip'].split('.')
            # Vary last octet slightly to simulate DHCP/dynamic IP
            last_octet = int(base_octets[-1]) + random.randint(-10, 10)
            last_octet = max(1, min(254, last_octet))  # Keep in valid range
            ip_address = f"{'.'.join(base_octets[:-1])}.{last_octet}"
        
        ping = {
            'timestamp': timestamp.isoformat(),
            'lat': lat,
            'lon': lon,
            'ad_id': ad_id,
            'service': service,
            'ip_address': ip_address,
            'name': person['name'],
            'device_type': random.choice(['mobile', 'tablet', 'desktop']),
            'user_agent': random.choice([
                'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)',
                'Mozilla/5.0 (Android 11; Mobile; rv:92.0)',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/93.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1'
            ]),
            'is_chaff': is_chaff
        }
        
        return ping
    
    def inject_chaff(self, protected_person, timestamp, num_chaff=5):
        """Inject chaff pings for a protected person"""
        chaff_pings = []
        for _ in range(num_chaff):
            chaff_ping = self.generate_location_ping(protected_person, timestamp, is_chaff=True)
            chaff_pings.append(chaff_ping)
        return chaff_pings
    
    def simulate_time_step(self, timestamp):
        """Simulate one time step of location pings + chaff injection"""
        all_pings = []
        step_real_locs = {'lons': [], 'lats': []}
        step_chaff_locs = {'lons': [], 'lats': []}
        
        # Generate real pings for all population
        for person in self.population:
            real_ping = self.generate_location_ping(person, timestamp, is_chaff=False)
            all_pings.append(real_ping)
            
            # Collect for visualization
            if person['is_protected']:
                step_real_locs['lons'].append(real_ping['lon'])
                step_real_locs['lats'].append(real_ping['lat'])
                
                # Add sample messages to terminal feed - much higher chance for REAL events
                if random.random() < 0.5:  # 50% chance to show REAL events in terminal
                    ip_masked = real_ping['ip_address'].split('.')
                    ip_display = f"{ip_masked[0]}..{ip_masked[2]}.{ip_masked[3]}"
                    self.add_terminal_message(f"REAL: {real_ping['name'][:15]} via {real_ping['service'][:12]} IP:{ip_display}")
            
            # Also show some non-protected users for realism
            elif random.random() < 0.2:  # 20% chance to show non-protected users
                ip_masked = real_ping['ip_address'].split('.')
                ip_display = f"{ip_masked[0]}..{ip_masked[2]}.{ip_masked[3]}"
                self.add_terminal_message(f"REAL: {real_ping['name'][:15]} via {real_ping['service'][:12]} IP:{ip_display}")
            
            # Add to profiles for T&T system (use the ad_id from the ping)
            self.profiles[real_ping['ad_id']].append(real_ping)
        
        # Inject chaff for protected individuals
        chaff_injected = 0
        if self.current_chaff_rate > 0:
            for person in self.population:
                if person['is_protected'] and random.random() < self.current_chaff_rate:
                    num_chaff = random.randint(1, 8)  # Variable chaff volume
                    chaff_pings = self.inject_chaff(person, timestamp, num_chaff)
                    all_pings.extend(chaff_pings)
                    chaff_injected += len(chaff_pings)
                    
                    # Collect chaff for visualization
                    for chaff_ping in chaff_pings:
                        step_chaff_locs['lons'].append(chaff_ping['lon'])
                        step_chaff_locs['lats'].append(chaff_ping['lat'])
                        self.profiles[chaff_ping['ad_id']].append(chaff_ping)
                        
                        # Add chaff messages to terminal - lower chance than REAL
                        if random.random() < 0.1:  # 10% chance to show chaff in terminal
                            ip_masked = chaff_ping['ip_address'].split('.')
                            ip_display = f"{ip_masked[0]}..{ip_masked[2]}.{ip_masked[3]}"
                            self.add_terminal_message(f"CHAFF: {chaff_ping['name'][:15]} via {chaff_ping['service'][:12]} IP:{ip_display}")
        
        # Add status messages less frequently
        if chaff_injected > 0 and random.random() < 0.3:  # 30% chance to show chaff injection status
            self.add_terminal_message(f"MITHRIL: Injected {chaff_injected} chaff pings ({self.current_chaff_rate*100:.0f}% rate)")
        
        # Update live location data (keep last 100 points for performance)
        self.live_real_locs['lons'].extend(step_real_locs['lons'])
        self.live_real_locs['lats'].extend(step_real_locs['lats'])
        self.live_chaff_locs['lons'].extend(step_chaff_locs['lons'])
        self.live_chaff_locs['lats'].extend(step_chaff_locs['lats'])
        
        # Keep only recent data for performance
        max_points = 200
        if len(self.live_real_locs['lons']) > max_points:
            self.live_real_locs['lons'] = self.live_real_locs['lons'][-max_points:]
            self.live_real_locs['lats'] = self.live_real_locs['lats'][-max_points:]
        if len(self.live_chaff_locs['lons']) > max_points:
            self.live_chaff_locs['lons'] = self.live_chaff_locs['lons'][-max_points:]
            self.live_chaff_locs['lats'] = self.live_chaff_locs['lats'][-max_points:]
        
        return all_pings
    
    def targeting_tracking_system(self, tolerance=0.01):
        """
        Toy T&T system that tries to match ad_ids to location patterns
        Returns true_positive_rate for protected individuals
        """
        correct_matches = 0
        total_attempts = 0
        false_positives = 0
        
        for person in self.population:
            if not person['is_protected']:
                continue
                
            true_location = (person['true_lat'], person['true_lon'])
            
            # Check all ad_ids for this person
            for identity in person['tracking_identities']:
                ad_id = identity['ad_id']
                
                # T&T system tries to predict location based on profile
                if ad_id in self.profiles and len(self.profiles[ad_id]) > 0:
                    recent_pings = self.profiles[ad_id][-10:]  # Last 10 pings
                    
                    # Simple centroid-based prediction
                    avg_lat = np.mean([ping['lat'] for ping in recent_pings])
                    avg_lon = np.mean([ping['lon'] for ping in recent_pings])
                    predicted_location = (avg_lat, avg_lon)
                    
                    # Check if prediction is close to true location
                    distance = np.sqrt((true_location[0] - predicted_location[0])**2 + 
                                     (true_location[1] - predicted_location[1])**2)
                    
                    total_attempts += 1
                    if distance < tolerance:
                        correct_matches += 1
                    
                    # Count false positives (chaff-influenced predictions)
                    chaff_count = sum(1 for ping in recent_pings if ping.get('is_chaff', False))
                    if chaff_count > 0:
                        false_positives += 1
        
        true_positive_rate = correct_matches / max(total_attempts, 1)
        false_positive_rate = false_positives / max(total_attempts, 1)
        
        # Add terminal message for significant accuracy changes
        if hasattr(self, 'last_tp_rate'):
            accuracy_change = abs(true_positive_rate - self.last_tp_rate)
            if accuracy_change > 0.1:  # 10% change
                direction = "↓" if true_positive_rate < self.last_tp_rate else "↑"
                self.add_terminal_message(f"T&T: Accuracy {direction} {true_positive_rate*100:.1f}% (Δ{accuracy_change*100:.1f}%)")
        
        self.last_tp_rate = true_positive_rate
        
        return true_positive_rate, false_positive_rate
    
    def print_sample_data(self):
        """Print some sample tracking data to show realistic identifiers"""
        print("\n📋 SAMPLE TRACKING DATA:")
        print("=" * 80)
        
        sample_people = random.sample(self.population[:10], min(5, len(self.population)))
        
        for person in sample_people:
            print(f"👤 {person['name']}")
            
            # Show all tracking identities for this person
            for i, identity in enumerate(person['tracking_identities']):
                if i == 0:
                    print(f"   🏷️  Tracking Service: {identity['service']}")
                    print(f"   🆔 Ad ID: {identity['ad_id']}")
                else:
                    print(f"   🏷️  Tracking Service: {identity['service']}")
                    print(f"   🆔 Ad ID: {identity['ad_id']}")
            
            # Format IP to match user's example with partial masking
            ip_parts = person['base_ip'].split('.')
            if len(ip_parts) == 4:
                masked_ip = f"{ip_parts[0]}..{ip_parts[2]}.{ip_parts[3]}"
            else:
                masked_ip = person['base_ip']
            
            print(f"   🌐 Base IP: {masked_ip}")
            print(f"   🚶 Movement Pattern: {person['movement_pattern']}")
            print(f"   🛡️  Protected: {'Yes' if person['is_protected'] else 'No'}")
            print()
    
    def setup_realtime_plots(self):
        """Initialize the real-time plotting interface"""
        plt.ion()  # Turn on interactive mode
        self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Load the map image
        self.load_map_image()
        
        # Plot 1: T&T Accuracy over time
        self.ax1.set_title('MITHRIL - Real-Time T&T System Accuracy', fontsize=14, fontweight='bold')
        self.ax1.set_xlabel('Time Steps')
        self.ax1.set_ylabel('Accuracy (%)')
        self.ax1.grid(True, alpha=0.3)
        self.ax1.set_ylim(0, 100)
        
        # Plot 2: Chaff Rate over time
        self.ax2.set_title('Chaff Injection Rate', fontsize=14, fontweight='bold')
        self.ax2.set_xlabel('Time Steps')
        self.ax2.set_ylabel('Chaff Rate (%)')
        self.ax2.grid(True, alpha=0.3)
        self.ax2.set_ylim(0, 100)
        
        # Plot 3: Live location visualization with map background
        self.ax3.set_title(f'Live Location Pings - {self.map_filename}', fontsize=14, fontweight='bold')
        self.ax3.set_xlabel('Longitude')
        self.ax3.set_ylabel('Latitude')
        self.ax3.set_xlim(self.min_lon, self.max_lon)
        self.ax3.set_ylim(self.min_lat, self.max_lat)
        
        # Add map as background if loaded
        if self.map_image:
            self.ax3.imshow(self.map_image, extent=[self.min_lon, self.max_lon, self.min_lat, self.max_lat], 
                           aspect='auto', alpha=0.7, zorder=0)
        
        # Plot 4: Terminal feed
        self.ax4.set_title('Live Surveillance Traffic Feed', fontsize=14, fontweight='bold')
        self.ax4.set_xlim(0, 1)
        self.ax4.set_ylim(0, 1)
        self.ax4.axis('off')  # Remove axes for terminal look
        
        # Set black background for terminal feel
        self.ax4.set_facecolor('black')
        
        # Add initial terminal messages
        self.add_terminal_message("MITHRIL: System initialized")
        self.add_terminal_message(f"MITHRIL: Tracking {self.population_size} subjects")
        self.add_terminal_message(f"MITHRIL: {len([p for p in self.population if p['is_protected']])} protected users")
        
        plt.tight_layout()
        plt.show(block=False)
        
    def update_plots(self):
        """Update all plots with current data"""
        if not self.realtime_stats['timestamps']:
            return
            
        # Clear axes 1-3 only (preserve terminal in ax4)
        self.ax1.clear()
        self.ax2.clear() 
        self.ax3.clear()
        
        # Plot 1: T&T Accuracy
        if len(self.realtime_stats['true_positive_rates']) > 0:
            accuracy_percentages = [tp*100 for tp in self.realtime_stats['true_positive_rates']]
            self.ax1.plot(range(len(accuracy_percentages)), accuracy_percentages, 'ro-', linewidth=2, markersize=6)
            self.ax1.fill_between(range(len(accuracy_percentages)), accuracy_percentages, alpha=0.3, color='red')
        
        self.ax1.set_title('MITHRIL - Real-Time T&T System Accuracy', fontsize=14, fontweight='bold')
        self.ax1.set_xlabel('Time Steps')
        self.ax1.set_ylabel('Accuracy (%)')
        self.ax1.grid(True, alpha=0.3)
        self.ax1.set_ylim(0, 100)
        
        # Add current accuracy text
        if self.realtime_stats['true_positive_rates']:
            current_acc = self.realtime_stats['true_positive_rates'][-1] * 100
            self.ax1.text(0.02, 0.98, f'Current: {current_acc:.1f}%', 
                         transform=self.ax1.transAxes, fontsize=12, 
                         verticalalignment='top', fontweight='bold',
                         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Plot 2: Chaff Rate
        if len(self.realtime_stats['chaff_rates']) > 0:
            chaff_percentages = [cr*100 for cr in self.realtime_stats['chaff_rates']]
            self.ax2.plot(range(len(chaff_percentages)), chaff_percentages, 'bo-', linewidth=2, markersize=6)
            self.ax2.fill_between(range(len(chaff_percentages)), chaff_percentages, alpha=0.3, color='blue')
        
        self.ax2.set_title('Chaff Injection Rate', fontsize=14, fontweight='bold')
        self.ax2.set_xlabel('Time Steps')
        self.ax2.set_ylabel('Chaff Rate (%)')
        self.ax2.grid(True, alpha=0.3)
        self.ax2.set_ylim(0, 100)
        
        # Add current chaff rate text
        if self.realtime_stats['chaff_rates']:
            current_chaff = self.realtime_stats['chaff_rates'][-1] * 100
            self.ax2.text(0.02, 0.98, f'Current: {current_chaff:.1f}%', 
                         transform=self.ax2.transAxes, fontsize=12, 
                         verticalalignment='top', fontweight='bold',
                         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Plot 3: Location visualization with map background
        self.ax3.set_xlim(self.min_lon, self.max_lon)
        self.ax3.set_ylim(self.min_lat, self.max_lat)
        
        # Re-add map background
        if self.map_image:
            self.ax3.imshow(self.map_image, extent=[self.min_lon, self.max_lon, self.min_lat, self.max_lat], 
                           aspect='auto', alpha=0.7, zorder=0)
        
        # Add location points on top of map
        if self.live_real_locs['lons']:
            self.ax3.scatter(self.live_real_locs['lons'], self.live_real_locs['lats'], 
                           c='blue', alpha=0.8, s=25, label='Real Locations', zorder=2, edgecolors='white', linewidth=0.5)
        
        if self.live_chaff_locs['lons']:
            self.ax3.scatter(self.live_chaff_locs['lons'], self.live_chaff_locs['lats'], 
                           c='red', alpha=0.6, s=20, label='Chaff Locations', zorder=1, edgecolors='white', linewidth=0.5)
        
        self.ax3.set_title(f'Live Location Pings - {self.map_filename}', fontsize=14, fontweight='bold')
        self.ax3.set_xlabel('Longitude')
        self.ax3.set_ylabel('Latitude')
        self.ax3.legend()
        
        # Plot 4: Update terminal feed
        self.ax4.clear()
        self.ax4.set_xlim(0, 1)
        self.ax4.set_ylim(0, 1)
        self.ax4.axis('off')
        self.ax4.set_facecolor('black')
        
        # Display terminal messages
        line_height = 1.0 / self.max_terminal_lines
        for i, message in enumerate(reversed(self.terminal_feed[-self.max_terminal_lines:])):
            y_pos = 0.95 - (i * line_height)
            
            # Color code different message types
            color = 'white'
            if 'CHAFF:' in message:
                color = '#ff6b6b'  # Light red
            elif 'REAL:' in message:
                color = '#74c0fc'  # Light blue
            elif 'T&T:' in message:
                color = '#ffd43b'  # Yellow
            elif 'MITHRIL:' in message:
                color = '#51cf66'  # Green
            elif 'MAP:' in message:
                color = '#ff8cc8'  # Pink
            
            self.ax4.text(0.02, y_pos, message, transform=self.ax4.transAxes, 
                         fontsize=9, fontfamily='monospace', color=color,
                         verticalalignment='top')
        
        plt.tight_layout()
        plt.draw()
        plt.pause(0.01)  # Small pause to allow GUI update
    
    def run_realtime_simulation(self, duration_minutes=10, chaff_schedule=None):
        """Run real-time simulation with live visualization"""
        print(f"🛡️  PROJECT MITHRIL: Real-Time Cloaking Demonstration - {self.map_filename}")
        print("=" * 60)
        print("🎯 Simulating realistic ad tracking with major surveillance platforms...")
        
        # Show sample data first
        self.print_sample_data()
        
        if chaff_schedule is None:
            # Default schedule: gradual increase in chaff rate
            chaff_schedule = [
                (0, 0.0),      # 0% for first phase
                (0.3, 0.2),    # 20% chaff
                (0.5, 0.5),    # 50% chaff  
                (0.7, 0.8),    # 80% chaff
                (0.9, 0.0),    # Back to 0% to show recovery
            ]
        
        self.setup_realtime_plots()
        
        start_time = datetime.now()
        time_step = timedelta(seconds=30)  # 30-second steps for smoother animation
        current_time = start_time
        
        total_steps = int(duration_minutes * 60 / 30)  # 30-second steps
        total_data_points = 0
        
        print(f"🚀 Starting {duration_minutes}-minute detailed surveillance observation...")
        print("📊 Watch how chaff injection confuses tracking systems in real-time!")
        print("📺 Terminal feed shows detailed live surveillance traffic...")
        print("⏱️  Slower paced for detailed observation of tracking patterns...")
        print("\n⏱️  Live Status Updates:")
        
        self.add_terminal_message("SIMULATION: Starting real-time demo")
        
        for step in range(total_steps):
            # Update chaff rate based on schedule
            old_chaff_rate = self.current_chaff_rate
            progress = step / total_steps
            for phase_progress, chaff_rate in chaff_schedule:
                if progress >= phase_progress:
                    self.current_chaff_rate = chaff_rate
            
            # Log chaff rate changes
            if self.current_chaff_rate != old_chaff_rate:
                self.add_terminal_message(f"CHAFF: Rate changed to {self.current_chaff_rate*100:.0f}%")
            
            # Generate pings for this time step
            pings = self.simulate_time_step(current_time)
            total_data_points += len(pings)
            
            # Test T&T system every few steps
            if step % 2 == 0:  # Test every minute
                tp_rate, fp_rate = self.targeting_tracking_system()
                
                # Store stats
                self.realtime_stats['timestamps'].append(current_time)
                self.realtime_stats['true_positive_rates'].append(tp_rate)
                self.realtime_stats['false_positive_rates'].append(fp_rate)
                self.realtime_stats['chaff_rates'].append(self.current_chaff_rate)
                self.realtime_stats['data_points_processed'].append(total_data_points)
                
                # Update plots
                self.update_plots()
                
                # Print status update with sample tracking data
                if step % 15 == 0:  # Print every 7.5 minutes for slower simulation
                    elapsed_minutes = step * 0.5
                    print(f"   {elapsed_minutes:.1f}min - Chaff: {self.current_chaff_rate*100:.0f}% - T&T Accuracy: {tp_rate*100:.1f}% - Data Points: {total_data_points:,}")
                    self.add_terminal_message(f"STATUS: {elapsed_minutes:.1f}min elapsed, {total_data_points:,} data points")
            
            current_time += time_step
            time.sleep(1.5)  # Slow down 5x for better observation of surveillance traffic
        
        self.simulation_complete = True
        self.add_terminal_message("SIMULATION: Complete!")
        
        print("\n✅ Simulation complete! Final results:")
        
        if self.realtime_stats['true_positive_rates']:
            final_accuracy = self.realtime_stats['true_positive_rates'][-1] * 100
            min_accuracy = min(self.realtime_stats['true_positive_rates']) * 100
            max_reduction = 100 - min_accuracy
            
            print(f"   • Final T&T accuracy: {final_accuracy:.1f}%")
            print(f"   • Maximum accuracy reduction: {max_reduction:.1f}%")
            print(f"   • Total data points processed: {total_data_points:,}")
            print(f"   • Protection effectiveness: {min(max_reduction, 99.9):.1f}%")
            
            self.add_terminal_message(f"RESULTS: Max reduction {max_reduction:.1f}%, Final accuracy {final_accuracy:.1f}%")
            
            print(f"\n🎯 SURVEILLANCE SYSTEMS CONFUSED:")
            # Count all unique services across all tracking identities
            active_services = set()
            for person in self.population:
                for identity in person['tracking_identities']:
                    active_services.add(identity['service'])
            service_list = list(active_services)
            print(f"   • Tracking services affected: {', '.join(service_list[:3])}... ({len(active_services)} total)")
        
        print(f"\n🗺️  Map used: {self.map_filename}")
        print("🎯 Keep the window open to examine the results, then close to proceed to next simulation!")
        
        # Update plots one final time
        self.update_plots()
        
        # Keep plot window open for viewing
        plt.ioff()
        plt.show()

def main():
    """Run the detailed real-time Mithril demonstration with multiple maps"""
    print("Initializing Project Mithril detailed surveillance demonstration...")
    print("🔍 Creating realistic ad tracking surveillance scenario...")
    print("🗺️  Running 4 detailed simulations with different map backgrounds...")
    print("⏱️  Slower paced for detailed observation of surveillance patterns...")
    
    map_files = ["map1.png", "map2.png", "map3.png", "map4.png"]
    
    for i, map_filename in enumerate(map_files, 1):
        print(f"\n{'='*80}")
        print(f"🚀 DETAILED SIMULATION {i}/4: Using {map_filename}")
        print(f"{'='*80}")
        
        # Create demo with smaller population for smoother real-time performance
        demo = MithrilRealtimeDemo(population_size=50, map_filename=map_filename)
        
        # Run real-time simulation (4 minutes for slower, more detailed observation)
        demo.run_realtime_simulation(duration_minutes=4)
        
        # Clear memory
        del demo
        
        if i < len(map_files):
            print(f"\n⏳ Preparing detailed simulation {i+1}/{len(map_files)}...")
            time.sleep(3)
    
    print(f"\n🎉 All 4 detailed simulations complete!")
    print("🛡️  MITHRIL demonstrated across multiple geographical regions")
    print("📊 Each map showed detailed surveillance patterns and chaff effectiveness")

if __name__ == "__main__":
    main()