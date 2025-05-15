from Flask import Flask, request, jsonify, render_template
import random
import os
import google.generativeai as genai
import googlemaps # For Google Maps API
import json

app = Flask(__name__)
Scss(app)

# --- GEMINI AI CONFIGURATION ---
# (Keep your existing Gemini configuration - API Key and Model)
GEMINI_API_KEY = os.environ.get('AIzaSyAir5YifwRPkapXN7zF5ErkctshWNmpDUk') 
# ... (rest of your Gemini setup) ...
gemini_model = None # Will be initialized if key is present
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel(
            'gemini-1.5-flash-latest', # Or gemini-pro which supports function calling well
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            # For function calling, you'd define tools here or pass them in generate_content
        )
        print("Gemini model configured successfully.")
    except Exception as e:
        print(f"ERROR: Failed to configure Gemini AI: {e}")
# --- END GEMINI AI CONFIGURATION ---


# --- GOOGLE MAPS PLATFORM CONFIGURATION ---
Maps_PLATFORM_API_KEY = os.environ.get('AIzaSyAir5YifwRPkapXN7zF5ErkctshWNmpDUk')
gmaps_client = None
if Maps_PLATFORM_API_KEY:
    try:
        gmaps_client = googlemaps.Client(key=Maps_PLATFORM_API_KEY)
        print("Google Maps client configured successfully.")
    except Exception as e:
        print(f"ERROR: Failed to configure Google Maps client: {e}")
else:
    print("WARNING: Maps_PLATFORM_API_KEY not found. Real hospital search will be disabled.")
# --- END GOOGLE MAPS PLATFORM CONFIGURATION ---

# Fallback mocked hospitals
MOCKED_HOSPITALS = [
    {"name": "Simulated Central Hospital", "address": "123 Main St, Simulated City", "latitude": -6.1754, "longitude": 106.8272, "eta_min": 10, "eta_max": 15, "source": "mocked_data"},
    {"name": "Simulated Hope Clinic", "address": "456 Oak Ave, Simulated City", "latitude": -6.1750, "longitude": 106.8280, "eta_min": 12, "eta_max": 20, "source": "mocked_data"}
]

# This is the function Gemini would be told it can call (the "tool")
def get_nearby_hospitals_from_Maps(latitude, longitude, radius_meters=5000):
    """
    Finds nearby hospitals using Google Maps Places API.
    This function would be executed by your Python backend when Gemini requests it.
    """
    if not gmaps_client:
        print("Google Maps client not available. Returning mocked hospital data for tool call.")
        # Return a structure that mimics a real API error or limited data
        return {"error": "Google Maps service unavailable, mocked data used.", "hospitals": MOCKED_HOSPITALS[:1]}

    try:
        print(f"Google Maps API: Searching for hospitals near ({latitude},{longitude}), radius {radius_meters}m")
        places_result = gmaps_client.places_nearby(
            location=(latitude, longitude),
            radius=radius_meters,
            type='hospital' # You can also use keywords
        )

        hospitals = []
        if places_result and places_result.get('status') == 'OK':
            for place in places_result.get('results', []):
                hospitals.append({
                    "name": place.get('name'),
                    "address": place.get('vicinity', 'Address not available'),
                    "latitude": place['geometry']['location']['lat'],
                    "longitude": place['geometry']['location']['lng'],
                    "rating": place.get('rating', 'N/A'),
                    "open_now": place.get('opening_hours', {}).get('open_now', 'Unknown')
                })
            print(f"Google Maps API: Found {len(hospitals)} hospitals.")
            return {"hospitals": hospitals[:5]} # Return top 5 results for brevity
        else:
            print(f"Google Maps API: No results or error. Status: {places_result.get('status')}")
            return {"error": f"Could not find hospitals or API error: {places_result.get('status')}", "hospitals": []}

    except Exception as e:
        print(f"Google Maps API: Exception during call: {e}")
        return {"error": f"Exception calling Google Maps API: {str(e)}", "hospitals": []}

# Your existing symptom analysis function (can also be a tool for Gemini)
def analyze_symptoms_with_gemini_tool(symptoms_text):
    # ... (your existing Gemini symptom analysis prompt, but ensure it returns structured JSON)
    # For this example, let's assume it's similar to your previous one
    # and returns: {"ailment_guess": "...", "danger_level": "CRITICAL|EMERGENCY|URGENT|CONSULT_DOCTOR"}
    if not gemini_model:
        return {"error": "Symptom analysis AI not available."}
    
    prompt = f"""
    Analyze health symptoms. User says: "{symptoms_text}".
    Output JSON: {{"ailment_guess": "your guess", "danger_level": "CRITICAL|EMERGENCY|URGENT|CONSULT_DOCTOR"}}
    """ # Simplified prompt for brevity
    try:
        response = gemini_model.generate_content(prompt)
        # Basic parsing, robust parsing needed for real use
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_response)
    except Exception as e:
        return {"error": f"Symptom analysis AI error: {str(e)}"}

        def __repr__(self) -> str:
        return f"task (self.id)"


@app.route('/')
def dashboard_page_route():
    return render_template('dashboard.html') # Or your frontend HTML file name

@app.route('/buat-laporan') # Halaman untuk membuat laporan baru (frontend.html)
def new_report_page():
    return render_template('frontend.html')

@app.route('/api/orchestrate_emergency_response', methods=['POST'])
def orchestrate_emergency_response():
    if not gemini_model:
        return jsonify({"error": "AI Orchestrator is not available. Please check API key configuration."}), 503

    data = request.get_json()
    user_name = data.get('name', 'Anonymous User')
    symptoms = data.get('symptoms', '')
    user_lat = data.get('latitude')
    user_lon = data.get('longitude')

    if not symptoms or user_lat is None or user_lon is None:
        return jsonify({"error": "Symptoms and location (latitude, longitude) are required."}), 400
    
    try:
        user_lat = float(user_lat)
        user_lon = float(user_lon)
    except ValueError:
        return jsonify({"error": "Latitude and longitude must be numbers."}), 400

    # Define the tools Gemini can use
    tools = [
        {
            "function_declarations": [
                {
                    "name": "get_nearby_hospitals_from_Maps",
                    "description": "Gets a list of nearby hospitals based on latitude, longitude, and search radius.",
                    "parameters": {
                        "type_": "OBJECT", # Using type_ to avoid keyword conflict
                        "properties": {
                            "latitude": {"type_": "NUMBER", "description": "User's current latitude."},
                            "longitude": {"type_": "NUMBER", "description": "User's current longitude."},
                            "radius_meters": {"type_": "INTEGER", "description": "Search radius in meters, e.g., 5000 for 5km."}
                        },
                        "required": ["latitude", "longitude"]
                    }
                },
                {
                    "name": "analyze_symptoms_with_gemini_tool",
                    "description": "Analyzes user's symptoms to provide a general indication and emergency level.",
                    "parameters": {
                        "type_": "OBJECT",
                        "properties": {
                            "symptoms_text": {"type_": "STRING", "description": "The user's description of their symptoms."}
                        },
                        "required": ["symptoms_text"]
                    }
                }
            ]
        }
    ]
    
    # Initial prompt to Gemini to orchestrate
    # This prompt needs to guide Gemini on the overall flow
    orchestration_prompt = f"""
    You are an emergency response AI orchestrator.
    A user named '{user_name}' has provided symptoms: "{symptoms}".
    Their current location is latitude: {user_lat}, longitude: {user_lon}.

    Follow these steps:
    1. First, analyze the user's symptoms using the 'analyze_symptoms_with_gemini_tool'.
    2. Based on the danger level from the symptom analysis:
       - If the danger level is CRITICAL or EMERGENCY, then find nearby hospitals using the 'get_nearby_hospitals_from_Maps' tool. Use a radius of 5000 meters.
       - If the danger level is URGENT or CONSULT_DOCTOR, you do not need to find hospitals unless the user explicitly asks.
    3. Summarize all findings for the user. If hospitals were found, list the name of the first one.
       Provide a final JSON response like:
       {{"userName": "{user_name}", "symptomAnalysis": {{...symptom analysis result...}}, "hospitalSearchResults": {{...hospital search result...}} or null, "summary": "Your summary here." }}
    """
    
    # This is a simplified one-shot call. A real scenario might be multi-turn.
    # For proper tool use, you send the prompt and tools, Gemini might respond with a function call.
    # Then you execute it and send results back.
    
    # For simplicity, let's simulate the two-step process mostly in Python logic triggered by Gemini's first analysis.
    # --- Step 1: Symptom Analysis (using the dedicated function directly for now) ---
    symptom_analysis_result = analyze_symptoms_with_gemini_tool(symptoms)
    
    ailment_guess = "N/A"
    danger_level_raw = "CONSULT_DOCTOR" # Default
    danger_level_display = "CONSULT DOCTOR (GREEN)"

    if "error" not in symptom_analysis_result:
        ailment_guess = symptom_analysis_result.get("ailment_guess", "Could not determine.")
        danger_level_raw = symptom_analysis_result.get("danger_level", "CONSULT_DOCTOR")
        if danger_level_raw == "CRITICAL": danger_level_display = "CRITICAL (RED)"
        elif danger_level_raw == "EMERGENCY": danger_level_display = "EMERGENCY (ORANGE)"
        elif danger_level_raw == "URGENT": danger_level_display = "URGENT (YELLOW)"
        else: danger_level_display = "CONSULT DOCTOR (GREEN)"
    else: # Error from symptom analysis
        ailment_guess = symptom_analysis_result["error"]
        
    final_symptom_analysis_output = {"ailmentGuess": ailment_guess, "dangerLevel": danger_level_display}

    # --- Step 2: Hospital Search (if needed) ---
    hospital_search_results_for_gemini = None
    hospital_info_for_frontend = None
    eta_ambulance_for_frontend = "N/A"
    route_info_for_frontend = "Hospital search not performed or failed."

    if danger_level_raw in ["CRITICAL", "EMERGENCY"]:
        print(f"Danger level is {danger_level_raw}. Searching for hospitals...")
        # This is where you'd properly handle the multi-turn conversation if Gemini requested the tool.
        # For this example, we're calling our Python function directly.
        hospital_search_results_from_api = get_nearby_hospitals_from_Maps(user_lat, user_lon, radius_meters=5000)
        hospital_search_results_for_gemini = hospital_search_results_from_api # To potentially send back to Gemini for summary

        if "error" not in hospital_search_results_from_api and hospital_search_results_from_api.get("hospitals"):
            first_hospital = hospital_search_results_from_api["hospitals"][0]
            hospital_info_for_frontend = { # Data for your existing frontend structure
                "name": first_hospital["name"],
                "address": first_hospital["address"],
                "latitude": first_hospital["latitude"],
                "longitude": first_hospital["longitude"],
                "source": "Maps_places_api"
            }
            # ETA and Route info would ideally come from Directions API using this hospital's location
            eta_ambulance_for_frontend = f"{random.randint(5,20)}-{random.randint(20,35)} min (simulated)"
            route_info_for_frontend = f"Route from {first_hospital['name']} to you shown on map."
        elif "error" in hospital_search_results_from_api:
             route_info_for_frontend = f"Hospital search failed: {hospital_search_results_from_api['error']}"
        else:
            route_info_for_frontend = "No hospitals found nearby or API error."


    # --- Step 3: Generate Final Summary (conceptually, Gemini would do this if results were fed back) ---
    # For now, construct a basic summary in Python
    summary_parts = [f"Symptom analysis for {user_name}: {ailment_guess} (Severity: {danger_level_display})."]
    if hospital_info_for_frontend:
        summary_parts.append(f"Nearest hospital found: {hospital_info_for_frontend['name']} at {hospital_info_for_frontend['address']}.")
    elif danger_level_raw in ["CRITICAL", "EMERGENCY"]:
        summary_parts.append(f"Attempted to find hospitals, but {route_info_for_frontend.lower()}")
    
    final_summary = " ".join(summary_parts)

    # Prepare response for your frontend (matching its expected structure as much as possible)
    response_to_frontend = {
        "userName": user_name,
        "ailmentGuess": ailment_guess,
        "dangerLevel": danger_level_display,
        "ambulanceETA": eta_ambulance_for_frontend,
        "hospitalInfo": hospital_info_for_frontend, # This could be the first hospital object
        "userLocation": {"latitude": user_lat, "longitude": user_lon},
        "routeInfo": route_info_for_frontend,
        "mapPlaceholderMessage": "Map will display route if hospital is found.",
        "_orchestrationDetails": { # Optional: for debugging or more detailed UI
            "symptomAnalysisRaw": symptom_analysis_result,
            "hospitalSearchRaw": hospital_search_results_for_gemini,
            "finalSummaryByApp": final_summary
        }
    }
    return jsonify(response_to_frontend)


# Di Backend.py
DEBUG_MODE = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
# ...
if __name__ == '__main__':
    # Baris app.run() ini hanya untuk pengembangan lokal
    app.run(host='0.0.0.0', port=5000, debug=DEBUG_MODE)
