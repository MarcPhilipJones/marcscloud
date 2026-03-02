"""Example GPIO script for Raspberry Pi.

This script demonstrates basic GPIO operations.
Note: This will only work on a Raspberry Pi with RPi.GPIO installed.
"""

import sys

# Check if running on Raspberry Pi
try:
    import RPi.GPIO as GPIO
    ON_PI = True
except ImportError:
    ON_PI = False
    print("Not running on Raspberry Pi - GPIO functions will be simulated")


def setup_gpio() -> None:
    """Set up GPIO pins."""
    if ON_PI:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
    else:
        print("[Simulated] GPIO setup complete")


def led_on(pin: int) -> None:
    """Turn on an LED connected to the specified pin."""
    if ON_PI:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)
    else:
        print(f"[Simulated] LED on pin {pin} turned ON")


def led_off(pin: int) -> None:
    """Turn off an LED connected to the specified pin."""
    if ON_PI:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
    else:
        print(f"[Simulated] LED on pin {pin} turned OFF")


def cleanup() -> None:
    """Clean up GPIO resources."""
    if ON_PI:
        GPIO.cleanup()
    else:
        print("[Simulated] GPIO cleanup complete")


def main() -> None:
    """Main entry point."""
    print("Raspberry Pi GPIO Example")
    print("=" * 40)
    
    setup_gpio()
    
    # Example: Blink LED on GPIO pin 17
    led_pin = 17
    print(f"Testing LED on pin {led_pin}...")
    
    led_on(led_pin)
    print("LED is ON")
    
    led_off(led_pin)
    print("LED is OFF")
    
    cleanup()
    print("Done!")


if __name__ == "__main__":
    main()
