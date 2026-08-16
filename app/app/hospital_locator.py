import streamlit as st
import urllib.parse
from typing import List, Tuple, Dict, Optional
import time

def get_current_location() -> Optional[Tuple[float, float]]:
    """
    Get current location using browser geolocation API.
    Returns: Tuple of (latitude, longitude) or None if location not available
    """
    try:
        # Use Streamlit's built-in geolocation (if available in future versions)
        # For now, we'll use a placeholder that will be handled by the UI
        return None
    except Exception as e:
        st.error(f"Error getting current location: {e}")
        return None

def get_location_from_address(address: str) -> Optional[Tuple[float, float]]:
    """
    Convert address to coordinates using Nominatim (OpenStreetMap).

    Args:
        address: Address string to geocode

    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    try:
        from geopy.geocoders import Nominatim
        # Initialize Nominatim geocoder
        geolocator = Nominatim(user_agent="medical_chatbot")

        # Add delay to respect rate limits
        time.sleep(1)

        location = geolocator.geocode(address, timeout=10)
        if location:
            return location.latitude, location.longitude
        else:
            st.error(f"Could not find coordinates for: {address}")
            return None

    except Exception as e:
        st.error(f"Error geocoding address: {e}")
        return None

def show_google_maps_link(location: str):
    """
    Display a link to Google Maps for hospital search.

    Args:
        location: Location to search for hospitals
    """
    st.subheader(f"🏥 Hospitals near {location}")

    # Create search query for hospitals
    search_query = f"hospitals near {location}"
    encoded_query = urllib.parse.quote(search_query)

    # Create Google Maps URL
    maps_url = f"https://www.google.com/maps/search/{encoded_query}"

    # Display a clickable button that opens Google Maps
    st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <a href="{maps_url}" target="_blank" style="
            display: inline-block;
            background-color: #4285F4;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        ">
            🗺️ Open Google Maps for Hospital Search
        </a>
        <p style="margin-top: 15px; color: #666; font-size: 14px;">
            Click the button above to open Google Maps and find hospitals near {location}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Add some helpful information
    st.info("💡 **How to use:** Click the button above to open Google Maps in a new tab. The map will automatically search for hospitals in your specified location.")

def find_nearest_hospitals(location_input: str = "", use_current_location: bool = False,
                          radius: int = 5000, hospital_type: str = "hospital") -> Tuple[List[Dict], Optional[Tuple[float, float]]]:
    """
    Main function to find nearest hospitals using Google Maps embed.

    Args:
        location_input: Address or city name (used if not using current location)
        use_current_location: Whether to use browser geolocation
        radius: Search radius in meters (not used with Google Maps embed)
        hospital_type: Type of hospital to search for (not used with Google Maps embed)

    Returns:
        Tuple of (empty_list, center_coordinates)
    """
    # Determine location to search from
    if use_current_location:
        st.info("🌍 Detecting your current location...")
        current_loc = get_current_location()

        if current_loc:
            st.success("✅ Current location detected!")
            lat, lng = current_loc
            location_name = "Your Current Location"
        else:
            st.warning("⚠️ Could not detect current location. Please enter location manually.")
            if not location_input:
                return [], None
            lat, lng = get_location_from_address(location_input)
            location_name = location_input
    else:
        if not location_input:
            st.error("Please enter a location or enable current location detection.")
            return [], None

        location_result = get_location_from_address(location_input)
        if location_result is None:
            st.error(f"Could not find coordinates for: {location_input}")
            return [], None

        lat, lng = location_result
        location_name = location_input

    if not lat or not lng:
        st.error(f"Could not find coordinates for: {location_input or 'current location'}")
        return [], None

    # Display Google Maps link
    show_google_maps_link(location_name)

    return [], (lat, lng)
