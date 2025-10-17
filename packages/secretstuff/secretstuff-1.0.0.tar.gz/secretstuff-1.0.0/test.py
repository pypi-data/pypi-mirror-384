from secretstuff import SecretStuffPipeline

pipeline = SecretStuffPipeline()

# Process complete files
# redact_result = pipeline.process_text_file(
#     input_file="outs/test.txt",
#     output_redacted="outs/redacted.txt",
#     output_identified="outs/entities.json",
#     output_mapping="outs/mapping.json"
# )
# print(redact_result)
# # Reverse from files
# reverse_result = pipeline.reverse_from_files("outs/updated_afterCloudcall.txt", "outs/mapping.json", "outs/final.txt")
# print(reverse_result)

text = """
Mr. John Doe lives at 123 Main Street, New York, NY 10001.
His phone number is +1-555-123-4567 and email is john.doe@email.com.
His Aadhaar number is 1234 5678 9012 and PAN is ABCDE1234F.
"""

# Step 1: Just identify PII
entities = pipeline.identify_pii(text)
print("ENTITIES:")
print(entities)

# Step 2: Redact when ready
redacted_text = pipeline.redact_pii(text)
print("REDACTED TEXT:")
print(redacted_text)


processed_text= """
Hi [NAME REDACTED2],

I hope you’re doing well.
Below are your contact and identification details for our records:

Address: LOC_0

Phone: +1-555-123-4567

Email: [NAME REDACTED3]

Aadhaar Number: CODE_0

PAN: CODE_1

Please review and confirm if all the above information is correct.
"""
# Step 3: Reverse after processing
restored_text, _, _ = pipeline.reverse_redaction(processed_text)
print("RESTORED TEXT:")
print(restored_text)