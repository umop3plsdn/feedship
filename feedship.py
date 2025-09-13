import requests
import re
import sys
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

def debug_print(message, level="INFO"):
    """Print debug messages with different levels"""
    colors = {
        "INFO": "\033[94m",    # Blue
        "SUCCESS": "\033[92m", # Green
        "WARNING": "\033[93m", # Yellow
        "ERROR": "\033[91m",   # Red
        "RESET": "\033[0m"     # Reset
    }
    print(f"{colors.get(level, colors['RESET'])}[{level}] {message}{colors['RESET']}")

def get_youtube_rss(channel_url):
    """
    Extract RSS feed URL from a YouTube channel URL with detailed debugging
    """
    debug_print(f"Starting RSS extraction for: {channel_url}")
    
    # Validate URL format
    if not channel_url.startswith(('http://', 'https://')):
        channel_url = 'https://' + channel_url
        debug_print(f"Added https:// prefix: {channel_url}", "WARNING")
    
    if 'youtube.com' not in channel_url and 'youtu.be' not in channel_url:
        debug_print("URL doesn't appear to be a YouTube URL", "ERROR")
        return None
    
    try:
        debug_print("Making request to YouTube...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(channel_url, headers=headers, timeout=15)
        debug_print(f"Received response: HTTP {response.status_code}")
        
        if response.status_code != 200:
            debug_print(f"Failed to retrieve page. Status code: {response.status_code}", "ERROR")
            return None
        
        debug_print("Parsing HTML content...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for channel ID in multiple potential locations
        channel_id = None
        debug_print("Searching for channel ID...")
        
        # Method 1: Look for meta tags
        meta_tag = soup.find('meta', {'property': 'channelId'}) or soup.find('meta', {'itemprop': 'channelId'})
        if meta_tag and meta_tag.get('content'):
            channel_id = meta_tag['content']
            debug_print(f"Found channel ID in meta tag: {channel_id}", "SUCCESS")
        
        # Method 2: Look for canonical link
        if not channel_id:
            canonical_link = soup.find('link', {'rel': 'canonical'})
            if canonical_link and canonical_link.get('href'):
                canonical_url = canonical_link['href']
                if '/channel/' in canonical_url:
                    channel_id = canonical_url.split('/channel/')[-1].split('/')[0]
                    debug_print(f"Found channel ID in canonical URL: {channel_id}", "SUCCESS")
        
        # Method 3: Look for JSON-LD data
        if not channel_id:
            json_ld = soup.find('script', {'type': 'application/ld+json'})
            if json_ld:
                debug_print("Found JSON-LD data, searching for channel ID...")
                # This is a simplified approach - in reality, you'd need to parse the JSON
                match = re.search(r'"channelId":"([^"]+)"', json_ld.string)
                if match:
                    channel_id = match.group(1)
                    debug_print(f"Found channel ID in JSON-LD: {channel_id}", "SUCCESS")
        
        # Method 4: Look for internal YouTube data
        if not channel_id:
            debug_print("Searching for internal YouTube data...")
            match = re.search(r'"channelId":"([^"]+)"', response.text)
            if match:
                channel_id = match.group(1)
                debug_print(f"Found channel ID in page text: {channel_id}", "SUCCESS")
        
        if not channel_id:
            debug_print("Could not find channel ID using any method", "ERROR")
            # Try to extract from URL directly as last resort
            if '/channel/' in channel_url:
                channel_id = channel_url.split('/channel/')[-1].split('/')[0]
                debug_print(f"Extracted channel ID from URL: {channel_id}", "WARNING")
            else:
                debug_print("No channel ID found. The channel might have restrictions.", "ERROR")
                return None
        
        # Construct RSS URL
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        debug_print(f"Generated RSS URL: {rss_url}", "SUCCESS")
        
        # Verify the RSS feed exists
        debug_print("Verifying RSS feed...")
        rss_response = requests.head(rss_url, timeout=10)
        if rss_response.status_code == 200:
            debug_print("RSS feed verified successfully!", "SUCCESS")
            return rss_url
        else:
            debug_print(f"RSS feed returned status code: {rss_response.status_code}", "WARNING")
            # Return the URL anyway as it might still work
            return rss_url
            
    except requests.exceptions.Timeout:
        debug_print("Request timed out. The server might be slow or unresponsive.", "ERROR")
        return None
    except requests.exceptions.ConnectionError:
        debug_print("Connection error. Please check your internet connection.", "ERROR")
        return None
    except requests.exceptions.RequestException as e:
        debug_print(f"Request failed: {str(e)}", "ERROR")
        return None
    except Exception as e:
        debug_print(f"Unexpected error: {str(e)}", "ERROR")
        return None

def main():
    """Main function to run the YouTube RSS extractor"""
    print("=" * 60)
    print("YouTube Channel RSS Feed Extractor")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # Use URL from command line argument
        channel_url = sys.argv[1]
    else:
        # Prompt for URL
        channel_url = input("Enter YouTube channel URL: ").strip()
    
    if not channel_url:
        debug_print("No URL provided. Exiting.", "ERROR")
        sys.exit(1)
    
    debug_print(f"Processing URL: {channel_url}")
    rss_url = get_youtube_rss(channel_url)
    
    print("\n" + "=" * 60)
    if rss_url:
        print(f"\n✅ RSS Feed URL: {rss_url}")
        print("\nYou can use this RSS URL with any RSS reader to get updates")
        print("from this YouTube channel.")
    else:
        print("\n❌ Failed to extract RSS URL.")
        print("\nPossible reasons:")
        print("- The channel might not exist or be unavailable")
        print("- The channel might have restrictions")
        print("- YouTube might have changed their page structure")
        print("- There might be a network issue")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
