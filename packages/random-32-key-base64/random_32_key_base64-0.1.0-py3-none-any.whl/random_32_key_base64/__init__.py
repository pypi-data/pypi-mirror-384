import base64
import sys
import urllib.request
import urllib.error


def generate_random_bytes(num_bytes: int = 32) -> bytes:
    """
    Generate random bytes using random.org API.
    
    Args:
        num_bytes: Number of random bytes to generate (default: 32)
        
    Returns:
        bytes: Random bytes from random.org
        
    Raises:
        RuntimeError: If the API request fails
    """
    url = f"https://www.random.org/cgi-bin/randbyte?nbytes={num_bytes}&format=f"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = response.read()
            return data
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to get random bytes from random.org: {e}")


def main() -> None:
    """
    Main entry point for the random-32-key-base64 command.
    Generates 32 random bytes from random.org and prints them as base64.
    """
    try:
        # Generate 32 random bytes from random.org
        random_bytes = generate_random_bytes()
        
        # Convert to base64
        base64_encoded = base64.b64encode(random_bytes).decode('ascii')
        
        # Print the result
        print(base64_encoded)
        
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
