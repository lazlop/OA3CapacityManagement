import matplotlib.pyplot as plt
import numpy as np
from IPython.display import clear_output
from time import sleep

import random
import matplotlib.pyplot as plt
from time import sleep

class HomeLoad:
    def __init__(self, reservation_capacity=5, intervals=96):
        """
        Initialize the VEN with:
        - reservation_capacity: Maximum capacity the VEN is subscribed to.
        - intervals: Number of 15-minute intervals in a day (default 96).
        """
        self.reservation_capacity = reservation_capacity
        self.intervals = intervals
        self.base_load_shape = []  
        self.reservation_load_shape = []  
        self.capacity_request = []
        self.generate_random_load_shape()
        self.generate_capacity_need()
        self.generate_reservation_load_shape()

    def generate_random_load_shape(self):
        """
        Generate a random load shape where each interval load is between 0 and reservation capacity.
        """
        self.base_load_shape = [random.uniform(0, self.reservation_capacity) for _ in range(self.intervals)]
        # print("VEN: Generated random load shape for the day.")

    def generate_capacity_need(self):
        event_start = random.choice(range(0,22))
        # event can last from 1-4 hours 
        max_duration = 6 if (event_start +6 < 25) else 25 - event_start
        event_end = event_start + random.choice(range(2,max_duration))
        capacity = 5
        # if a price comes back, coin flip on if they want to pay it, todo later
        self.generate_capacity_request(event_start, event_end, capacity)


    def generate_capacity_request(self, start_interval, end_interval, capacity):
        """
        Request additional capacity for a given range of intervals.
        
        Args:
        - start_interval (int): Start interval.
        - end_interval (int): End interval.
        - capacity (float or list): Additional capacity requested. 
          If a single value, it is applied to all intervals. If a list, it must match the range length.
        """
        # Ensure reservation_load_shape is initialized
        if not self.reservation_load_shape:
            self.reservation_load_shape = self.base_load_shape.copy()
        
        # Calculate the number of intervals in the range
        num_intervals = end_interval - start_interval

        # Handle single capacity value for all intervals
        if isinstance(capacity, (int, float)):
            capacity_list = [capacity] * num_intervals
        # Handle list of varying capacity levels
        elif isinstance(capacity, list):
            if len(capacity) != num_intervals:
                raise ValueError(f"Capacity list length ({len(capacity)}) does not match the interval range ({num_intervals}).")
            capacity_list = capacity
        else:
            raise ValueError("Capacity must be either a single value or a list.")

        # Apply the additional capacity to the reservation load shape
        self.capacity_request = []
        for i in range(start_interval, end_interval):
            self.reservation_load_shape[i] += capacity_list[i - (start_interval)]
            self.capacity_request.append((i, capacity_list[i - (start_interval)]))

        # print(f"VEN: Requested additional capacity from interval {start_interval} to {end_interval}.")

    def generate_reservation_load_shape(self):
        for (i, v) in self.capacity_request:
            self.reservation_load_shape[i] += v

    def clear_reservation_load_shape(self):
        self.reservation_load_shape = self.base_load_shape.copy()

    def adjust_capacity_request(self, capacity_increase_prices):
        """
        Adjust the capacity request based on the capacity increase price.
        For now, if price is greater than 0.2, we will not do capacity increase
        for that period
        
        Args:
        - capacity_increase_prices (list): List of hourly capacity prices from VTN.
        """
        new_capacity_request = []
        for i, price in enumerate(capacity_increase_prices):
            if price < 0.2:
                # append the capacity value 
                new_capacity_request.append(self.capacity_request[i][1])
            else:
                new_capacity_request.append(0)
        print("VEN: Adjusted capacity request based on capacity increase prices:", new_capacity_request)
        
        self.generate_capacity_request(self.capacity_request[0][0], self.capacity_request[-1][0] + 1, new_capacity_request)
                   
    def plot_load_shapes(self):
        """
        Plot the base load shape and the load shape with reservations.
        """
        intervals = range(1, self.intervals + 1)
        plt.figure(figsize=(12, 6))
        plt.plot(intervals, self.base_load_shape, label="Base Load Shape", color="blue", linewidth=2)
        plt.plot(intervals, self.reservation_load_shape, label="Load Shape with Reservations", color="orange", linestyle="--", linewidth=2)
        plt.axhline(y=self.reservation_capacity, color="red", linestyle=":", label="Reservation Limit")
        plt.title("VEN Load Shape and Reservations", fontsize=14)
        plt.xlabel("Interval (15 minutes each)", fontsize=12)
        plt.ylabel("Load (kW)", fontsize=12)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

def plot_home(home):
    # plotting single home 
    # 1 home 
    for i in range(1,24):
        clear_output(wait=True) 
        plt.figure(figsize=(10, 4))
        plt.plot([i for i in range(i)], home.base_load_shape[0:i], label="Base Load Shape", color="blue", linewidth=2)
        plt.plot([i for i in range(i)], home.reservation_load_shape[0:i], label="Load Shape with Reservations", color="orange", linestyle="--", linewidth=2)
        plt.plot([i for i in range(24)], [home.reservation_capacity for i in range(24)], color="red", linestyle=":", label="Reservation Limit")
        plt.title("VEN Load Shape and Reservations", fontsize=14)
        plt.xlabel("Interval (15 minutes each)", fontsize=12)
        plt.ylabel("Load (kW)", fontsize=12)
        plt.legend()
        plt.grid()
        plt.show()
        sleep(0.1)

def plot_many_homes(homes):
# plotting all combined homes 
    plt.close()
    for i in range(1, 24):
        clear_output(wait=True)
        combined_base_load = [sum(home.base_load_shape[j] for home in homes) for j in range(i)]
        combined_reservation_load = [sum(home.reservation_load_shape[j] for home in homes) for j in range(i)]
        
        plt.figure(figsize=(10, 4))
        plt.plot(range(i), combined_base_load, label="Combined Base Load Shape", color="blue", linewidth=2)
        plt.plot(range(i), combined_reservation_load, label="Combined Load Shape with Reservations", color="orange", linestyle="--", linewidth=2)
        # Plot reservation capacity line (assuming it's constant across intervals and homes)
        reservation_capacity_total = sum(home.reservation_capacity for home in homes)
        plt.plot(range(24), [reservation_capacity_total] * 24, color="red", linestyle=":", label="Combined Reservation Limit")
        plt.plot(range(24), [reservation_capacity_total*2/3] * 24, color="red", linewidth = '2', linestyle="solid", label="Substation Limit")
        
        # Add title and labels
        plt.title("Combined VEN Load Shape and Reservations", fontsize=14)
        plt.xlabel("Interval", fontsize=12)
        plt.ylabel("Load (kW)", fontsize=12)
        plt.ylim(0,70)
        plt.legend()
        plt.grid()
        plt.show()
        # Pause to simulate processing time (optional)
        sleep(0.1)