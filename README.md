# 🧠 Semantic Web–Based Intelligent Travel Planning Agent

An enhanced Semantic Web–powered intelligent travel-planning agent capable of **autonomously discovering, selecting, and composing services** — including **flights, hotels, and taxis** — using ontology-driven reasoning. The system ensures adaptive, end-to-end itinerary generation that aligns with user preferences such as dates, location, and budget.

---

## ✅ Key Features

✔ OWL-based travel domain ontology  
✔ RDF triple–based service representation  
✔ SPARQL query-driven semantic service discovery  
✔ Autonomous selection & composition of travel services  
✔ Flexible semantic reasoning for improved robustness  
✔ Nearby-city + alternative-date fallbacks  
✔ Budget-aware recommendations  
✔ End-to-end itinerary generation (flight → hotel → taxi)  
✔ Explanations of reasoning decisions  

---

## 🧩 System Overview

The agent uses:

### **1. Ontology (OWL)**
Models travel-related concepts:
- Service types (flight, hotel, taxi)
- Properties (destination, date, price, location)
- Constraints (availability, proximity)

This structured knowledge allows **machine-interpretable semantics** and ensures interoperability.

### **2. Knowledge Representation (RDF)**
All travel services (flights, hotels, taxis) are stored as **RDF triples**, enabling semantic querying rather than keyword search.

### **3. Semantic Reasoning (SPARQL + Logic Rules)**
SPARQL is used for:
- Service discovery
- Constraint validation
- Matching user input with available services
- Selecting alternatives when exact matches fail

---

## 🔍 Intelligent Reasoning Enhancements

The enhanced agent improves itinerary success probability using:

### ✅ Flexible Check-in Logic  
Hotels can be recommended **several days after arrival**, based on user preferences.

### ✅ Nearby-City Reasoning  
If no hotels are available in the destination city, nearby locations such as **Gurugram or Noida** are considered.

### ✅ Budget-Aware Decisions  
If options exceed budget:
- Recommends lower-cost alternatives
- Suggests hotels available on alternate dates

### ✅ Service Composition  
After selecting the hotel, taxis are chosen **based on hotel location**, ensuring end-to-end service flow.

---

## 🔗 Workflow

1. User provides:
   - Departure city
   - Destination
   - Travel date
   - Budget (optional)

2. Agent queries flights → selects best match

3. Agent queries hotels → applies:
   - Date compatibility
   - Location match
   - Flexible dates
   - Nearby-city fallback
   - Budget alignment

4. Agent selects taxi service near chosen hotel

5. Agent generates final itinerary + reasoning explanation  

Example Output:
Flight → Hotel → Taxi
