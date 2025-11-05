# app.py
# Streamlit GUI for Semantic Travel Booking Agent (Enhanced: flexible dates + nearby fallback)
# Requirements: rdflib, owlready2, streamlit
# Run: streamlit run app.py

import streamlit as st
from rdflib import Graph, Literal, RDF, Namespace
from rdflib.namespace import XSD, RDFS
from owlready2 import get_ontology, Thing, DataProperty, ObjectProperty
import os
from datetime import datetime, timedelta

OUTDIR = "semantic_agent_files"
os.makedirs(OUTDIR, exist_ok=True)

# ---------------------------
# Create ontology (if not present)
# ---------------------------
def create_ontology(outdir=OUTDIR):
    onto_path = os.path.join(outdir, "travel_ontology.owl")
    if os.path.exists(onto_path):
        return onto_path
    onto = get_ontology("http://example.org/travel_ontology.owl")
    with onto:
        class TravelService(Thing): pass
        class FlightService(TravelService): pass
        class HotelService(TravelService): pass
        class TaxiService(TravelService): pass

        class departureCity(DataProperty):
            domain = [FlightService]; range = [str]
        class arrivalCity(DataProperty):
            domain = [FlightService]; range = [str]
        class price(DataProperty):
            domain = [TravelService]; range = [int]
        class airline(DataProperty):
            domain = [FlightService]; range = [str]
        class location(DataProperty):
            domain = [HotelService]; range = [str]
        class rating(DataProperty):
            domain = [HotelService]; range = [float]
        class serviceDate(DataProperty):
            domain = [TravelService]; range = [str]
        class hasPart(ObjectProperty):
            domain = [TravelService]; range = [TravelService]

    onto.save(file=onto_path, format="rdfxml")
    return onto_path

# ---------------------------
# Build RDF graph (with more hotels + cities)
# ---------------------------
def build_graph(outdir=OUTDIR):
    g = Graph()
    TRAVEL = Namespace("http://example.org/travel#")
    g.bind("travel", TRAVEL)
    g.bind("xsd", XSD)
    g.bind("rdfs", RDFS)

    # Flights
    flights = [
        {"id": "Flight1", "dep": "Chennai", "arr": "Delhi", "price": 6500, "airline": "IndiGo", "date": "2025-11-05"},
        {"id": "Flight2", "dep": "Chennai", "arr": "Delhi", "price": 7200, "airline": "Air India", "date": "2025-11-05"},
        {"id": "Flight3", "dep": "Chennai", "arr": "Mumbai", "price": 5800, "airline": "Vistara", "date": "2025-11-05"},
        {"id": "Flight4", "dep": "Chennai", "arr": "Delhi", "price": 9000, "airline": "SpiceJet", "date": "2025-11-03"},
    ]
    for f in flights:
        furi = TRAVEL[f["id"]]
        g.add((furi, RDF.type, TRAVEL.FlightService))
        g.add((furi, TRAVEL.departureCity, Literal(f["dep"])))
        g.add((furi, TRAVEL.arrivalCity, Literal(f["arr"])))
        g.add((furi, TRAVEL.price, Literal(f["price"], datatype=XSD.integer)))
        g.add((furi, TRAVEL.airline, Literal(f["airline"])))
        g.add((furi, TRAVEL.serviceDate, Literal(f["date"], datatype=XSD.date)))

    # Hotels (added early availability + nearby cities)
    hotels = [
        # Delhi hotels (earlier + original)
        {"id":"Hotel0", "location":"Delhi", "price":2800, "rating":4.0, "available_from":"2025-11-01"},
        {"id":"Hotel1", "location":"Delhi", "price":3000, "rating":4.2, "available_from":"2025-11-05"},
        {"id":"Hotel2", "location":"Delhi", "price":2500, "rating":3.9, "available_from":"2025-11-05"},
        {"id":"Hotel4", "location":"Delhi", "price":4500, "rating":4.8, "available_from":"2025-11-06"},
        # Nearby NCR cities (Gurugram, Noida)
        {"id":"HotelG1", "location":"Gurugram", "price":2600, "rating":4.1, "available_from":"2025-11-03"},
        {"id":"HotelG2", "location":"Gurugram", "price":2200, "rating":3.8, "available_from":"2025-11-04"},
        {"id":"HotelN1", "location":"Noida", "price":2400, "rating":4.0, "available_from":"2025-11-02"},
        # Mumbai example
        {"id":"HotelM1", "location":"Mumbai", "price":2000, "rating":4.0, "available_from":"2025-11-05"},
    ]
    for h in hotels:
        huri = TRAVEL[h["id"]]
        g.add((huri, RDF.type, TRAVEL.HotelService))
        g.add((huri, TRAVEL.location, Literal(h["location"])))
        g.add((huri, TRAVEL.price, Literal(h["price"], datatype=XSD.integer)))
        g.add((huri, TRAVEL.rating, Literal(h["rating"])))
        g.add((huri, TRAVEL.serviceDate, Literal(h["available_from"], datatype=XSD.date)))

    # Taxis
    taxis = [
        {"id":"Taxi1", "city":"Delhi", "price":900},
        {"id":"Taxi2", "city":"Delhi", "price":1200},
        {"id":"TaxiG1", "city":"Gurugram", "price":1000},
        {"id":"Taxi3", "city":"Mumbai", "price":700}
    ]
    for t in taxis:
        turi = TRAVEL[t["id"]]
        g.add((turi, RDF.type, TRAVEL.TaxiService))
        g.add((turi, TRAVEL.city, Literal(t["city"])))
        g.add((turi, TRAVEL.price, Literal(t["price"], datatype=XSD.integer)))

    ttl_path = os.path.join(outdir, "travel_services.ttl")
    g.serialize(destination=ttl_path, format="turtle")
    return g

# ---------------------------
# Helper SPARQL runners
# ---------------------------
def run_sparql(graph, query, init_ns=None):
    initNs = {"xsd": XSD}
    if init_ns:
        initNs.update(init_ns)
    return graph.query(query, initNs=initNs)

# ---------------------------
# Agent planning (with flexible date and nearby fallback)
# ---------------------------
def plan_trip_enhanced(graph, departure, arrival, dep_date_str, budget, date_flex_days=2):
    # Convert date
    try:
        arrival_date = datetime.fromisoformat(dep_date_str).date()
    except:
        arrival_date = datetime.now().date()

    # 1. Find flights (ordered by price)
    q_flights = f"""
    PREFIX travel: <http://example.org/travel#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT ?flight ?price ?airline ?date
    WHERE {{
        ?flight a travel:FlightService ;
                travel:departureCity "{departure}" ;
                travel:arrivalCity "{arrival}" ;
                travel:price ?price ;
                travel:airline ?airline ;
                travel:serviceDate ?date .
    }}
    ORDER BY ASC(xsd:integer(?price))
    """
    flights = run_sparql(graph, q_flights)
    flight_candidates = []
    for r in flights:
        flight_candidates.append({
            "uri": str(r.flight),
            "price": int(r.price.toPython()),
            "airline": str(r.airline.toPython()),
            "date": str(r.date.toPython())
        })
    if not flight_candidates:
        return {"status":"NoFlights", "message":"No flights found for route."}

    # choose cheapest flight (or you could present options)
    best_flight = flight_candidates[0]
    flight_date = datetime.fromisoformat(best_flight["date"]).date()

    # 2. Try hotels in arrival city with flexible window (arrival_date .. arrival_date + date_flex_days)
    window_end = flight_date + timedelta(days=date_flex_days)
    q_hotels_city = f"""
    PREFIX travel: <http://example.org/travel#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT ?hotel ?price ?rating ?avail_date
    WHERE {{
        ?hotel a travel:HotelService ;
               travel:location "{arrival}" ;
               travel:price ?price ;
               travel:rating ?rating ;
               travel:serviceDate ?avail_date .
    }}
    ORDER BY ASC(xsd:integer(?price))
    """
    hotels_city = run_sparql(graph, q_hotels_city)
    hotel_candidates = []
    # collect all hotels then apply date logic in Python for flexibility & next-available
    next_available = None
    for r in hotels_city:
        avail = datetime.fromisoformat(str(r.avail_date.toPython())).date()
        price = int(r.price.toPython())
        rating = float(r.rating.toPython())
        hotel_candidates.append({
            "uri": str(r.hotel),
            "price": price,
            "rating": rating,
            "avail_date": avail
        })
        if avail >= flight_date:
            if next_available is None or avail < next_available["avail_date"]:
                next_available = {"uri": str(r.hotel), "price": price, "rating": rating, "avail_date": avail}

    # Filter candidates within flexible window
    within_window = [h for h in hotel_candidates if h["avail_date"] <= window_end and h["avail_date"] >= flight_date]
    # also accept hotels whose avail_date <= flight_date (earlier available)
    within_window += [h for h in hotel_candidates if h["avail_date"] <= flight_date and h not in within_window]
    # remove duplicates
    seen = set(); filtered = []
    for h in within_window:
        if h["uri"] not in seen:
            filtered.append(h); seen.add(h["uri"])

    chosen_hotel = None
    chosen_hotel_method = None
    if filtered:
        # sort by price then rating
        filtered_sorted = sorted(filtered, key=lambda h: (h["price"], -h["rating"]))
        chosen_hotel = filtered_sorted[0]
        chosen_hotel_method = "ExactCityWithinWindow"
    else:
        # 3. Nearby fallback (hybrid): immediate nearby cities list then region
        nearby_cities_immediate = ["Gurugram", "Noida"]  # immediate nearby NCR cities
        nearby_cities_region = ["Ghaziabad", "Faridabad"]  # extended region
        fallback_tried = []
        for nearby_group in (nearby_cities_immediate, nearby_cities_region):
            for city in nearby_group:
                fallback_tried.append(city)
                q_hotels_near = f"""
                PREFIX travel: <http://example.org/travel#>
                SELECT ?hotel ?price ?rating ?avail_date
                WHERE {{
                    ?hotel a travel:HotelService ;
                           travel:location "{city}" ;
                           travel:price ?price ;
                           travel:rating ?rating ;
                           travel:serviceDate ?avail_date .
                }}
                ORDER BY ASC(xsd:integer(?price))
                """
                hotels_near = run_sparql(graph, q_hotels_near)
                near_candidates = []
                next_avail_near = None
                for r in hotels_near:
                    avail = datetime.fromisoformat(str(r.avail_date.toPython())).date()
                    near_candidates.append({
                        "uri": str(r.hotel),
                        "price": int(r.price.toPython()),
                        "rating": float(r.rating.toPython()),
                        "avail_date": avail,
                        "city": city
                    })
                    if avail >= flight_date:
                        if next_avail_near is None or avail < next_avail_near["avail_date"]:
                            next_avail_near = {"uri": str(r.hotel), "price": int(r.price.toPython()), "rating": float(r.rating.toPython()), "avail_date": avail, "city": city}
                # choose hotel within flexible window in nearby city
                window_end = flight_date + timedelta(days=date_flex_days)
                within_near = [h for h in near_candidates if h["avail_date"] <= window_end and h["avail_date"] >= flight_date]
                within_near += [h for h in near_candidates if h["avail_date"] <= flight_date and h not in within_near]
                if within_near:
                    chosen_hotel = sorted(within_near, key=lambda h: (h["price"], -h["rating"]))[0]
                    chosen_hotel_method = f"NearbyCity:{city}"
                    break
                # else if no immediate availability, remember next available in this city
                if next_avail_near and chosen_hotel is None and chosen_hotel_method is None:
                    chosen_hotel = next_avail_near
                    chosen_hotel_method = f"NearbyCityNextAvail:{city}"
                    # do not break - prefer earlier group but we keep as fallback
            if chosen_hotel:
                break

    # 4. Taxi selection: prefer taxi in same city as chosen_hotel's city (extract city)
    q_taxi_base = f"""
    PREFIX travel: <http://example.org/travel#>
    SELECT ?taxi ?price ?city
    WHERE {{
        ?taxi a travel:TaxiService ;
              travel:city ?city ;
              travel:price ?price .
    }}
    ORDER BY ASC(xsd:integer(?price))
    """
    taxis = run_sparql(graph, q_taxi_base)
    taxi_candidates = []
    for r in taxis:
        taxi_candidates.append({"uri": str(r.taxi), "price": int(r.price.toPython()), "city": str(r.city.toPython())})
    # prefer taxi in chosen hotel's city if possible
    chosen_taxi = None
    if chosen_hotel:
        ch_city = None
        # attempt to extract city: if hotel uri contains location token or we saved city in chosen_hotel
        if "city" in chosen_hotel:
            ch_city = chosen_hotel["city"]
        else:
            # try reading hotel's location from graph via SPARQL
            q_loc = f"""
            PREFIX travel: <http://example.org/travel#>
            SELECT ?loc WHERE {{
                <{chosen_hotel['uri']}> travel:location ?loc .
            }} LIMIT 1
            """
            loc_res = run_sparql(graph, q_loc)
            for lr in loc_res:
                ch_city = str(lr.loc.toPython())
        # pick cheapest taxi in ch_city
        for t in taxi_candidates:
            if t["city"] == ch_city:
                chosen_taxi = t
                break
    if not chosen_taxi and taxi_candidates:
        chosen_taxi = taxi_candidates[0]

    # 5. Compute budget & decide final itinerary (allow explanation)
    if not chosen_hotel:
        return {"status":"NoHotelAnywhere", "message":"No hotel found in city or nearby; recommend adjusting date or city."}

    total_cost = best_flight["price"] + chosen_hotel["price"] + (chosen_taxi["price"] if chosen_taxi else 0)

    explanation = []
    explanation.append(f"Selected flight {best_flight['airline']} on {best_flight['date']} (₹{best_flight['price']}).")
    explanation.append(f"Hotel chosen method: {chosen_hotel_method}; hotel: {chosen_hotel['uri'].split('#')[-1]} available from {chosen_hotel['avail_date']} (₹{chosen_hotel['price']}).")
    if chosen_taxi:
        explanation.append(f"Taxi chosen: {chosen_taxi['uri'].split('#')[-1]} in {chosen_taxi['city']} (₹{chosen_taxi['price']}).")
    explanation.append(f"Estimated total cost: ₹{total_cost} (Your budget: ₹{budget}).")

    if total_cost <= int(budget):
        status = "OK"
    else:
        status = "OverBudget"

    return {
        "status": status,
        "flight": best_flight,
        "hotel": chosen_hotel,
        "taxi": chosen_taxi,
        "total_cost": total_cost,
        "explanation": explanation,
        "flight_candidates": flight_candidates
    }

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="Semantic Travel Booking Agent (Enhanced)", layout="centered")
st.title("Semantic Travel Booking Agent — Enhanced Demo")

st.markdown("""
This enhanced demo includes:
- flexible hotel check-in (flight date ± 2 days),
- nearby city fallback (Gurugram / Noida / region),
- next-available date suggestion,
- added hotel data for earlier availability.
""")

# create ontology + graph
create_ontology()
g = build_graph()

with st.form("trip"):
    col1, col2 = st.columns(2)
    with col1:
        dep = st.text_input("Departure City", value="Chennai")
        dep_date = st.date_input("Preferred Departure / Travel Date")
    with col2:
        arr = st.text_input("Arrival City", value="Delhi")
        ret_date = st.date_input("Return Date")
    budget = st.number_input("Budget (INR)", min_value=500, value=15000, step=500)
    flex_days = st.slider("Flexible days allowed after flight arrival for hotel check-in", 0, 5, 2)
    submitted = st.form_submit_button("Plan Trip")

if submitted:
    dep_date_str = dep_date.isoformat()
    st.info(f"Planning trip {dep} → {arr} on {dep_date_str} with budget ₹{budget}")
    res = plan_trip_enhanced(g, dep, arr, dep_date_str, budget, date_flex_days=flex_days)

    if res["status"] == "OK":
        st.success("Itinerary found ✔")
        st.write("**Flight:**", res["flight"]["airline"], "| Price: ₹"+str(res["flight"]["price"]), "| Date:", res["flight"]["date"])
        st.write("**Hotel:**", res["hotel"]["uri"].split("#")[-1], "| Price: ₹"+str(res["hotel"]["price"]), "| Available from:", str(res["hotel"]["avail_date"]))
        st.write("**Taxi:**", res["taxi"]["uri"].split("#")[-1], "| Price: ₹"+str(res["taxi"]["price"]), "| City:", res["taxi"]["city"])
        st.write("**Total Cost:** ₹", res["total_cost"])
        st.markdown("**Explanation / Reasoning:**")
        for line in res["explanation"]:
            st.write("-", line)
    elif res["status"] == "OverBudget":
        st.warning(f"Estimated total cost ₹{res['total_cost']} exceeds budget ₹{budget}.")
        st.markdown("**Explanation / Reasoning:**")
        for line in res["explanation"]:
            st.write("-", line)
        st.info("Options: increase budget, allow larger flexible window, or change dates/city.")
    elif res["status"] == "NoHotelAnywhere":
        st.error("No hotels available in city or nearby within flexible window.")
        st.write(res.get("message"))
        st.info("Try increasing flexible days slider, changing date, or choose nearby city manually.")
    else:
        st.error("No feasible itinerary found.")
        st.write(res.get("message", "Unknown reason."))

st.markdown("---")
st.caption("Files saved locally: travel_ontology.owl, travel_services.ttl (in ./semantic_agent_files/).")
