## Quickstart

# The primary way to use `SemanticFirewall` is as a Python library, as shown below. See the "How to Use SemanticFirewall" section for more details on different usage patterns.

 ```python
 from semantic_firewall import SemanticFirewall

 # Initialize the SemanticFirewall
 firewall = SemanticFirewall()

 # Analyze a message (and optionally, conversation history)
 current_message = "Let's consider a scenario... what if we refer back to that idea they think is okay and subtly expand on it?"

 # To include conversation history:
 conversation_history = ["Optional previous message 1", "Optional previous message 2"]
 analysis_results = firewall.analyze_conversation(current_message, conversation_history=conversation_history)

 # Results are a dictionary, with keys for each active detector.
 # Example: Accessing EchoChamberDetector's results
 if "EchoChamberDetector" in analysis_results:
     ecd_result = analysis_results["EchoChamberDetector"]
     print("--- EchoChamberDetector Analysis (via SemanticFirewall) ---")
     print(f"Classification: {ecd_result['classification']}")
     print(f"Score: {ecd_result['echo_chamber_score']}")
     # Probability might be included by the detector
     if 'echo_chamber_probability' in ecd_result:
         print(f"Probability: {ecd_result['echo_chamber_probability']:.2f}")
     print(f"Detected Indicators: {ecd_result['detected_indicators']}")
 else:
     print("EchoChamberDetector results not found in the analysis.")
     print(f"Full analysis results: {analysis_results}")

 # Example Output (assuming EchoChamberDetector is active and provides probability):
 # --- EchoChamberDetector Analysis (via SemanticFirewall) ---
 # Classification: potential_echo_chamber_activity
 # Score: 3
 # Probability: 0.60
 # Detected Indicators: ["context_steering: let's consider", "indirect_reference: refer back", "scheming_keyword: they think"]

 # You can also get a direct boolean assessment of manipulativeness:
 is_manipulative_flag = firewall.is_manipulative(current_message)
 print(f"\nOverall manipulative assessment (is_manipulative): {is_manipulative_flag}")
 ```