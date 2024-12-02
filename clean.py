import json

input_file = 'data.json'
output_file = 'data_cleaned.json'

try:
    # Replace 'detected_encoding' with the encoding detected earlier (e.g., 'utf-16')
    detected_encoding = 'utf-16'  # Example, replace with actual encoding

    # Read the file with the detected encoding
    with open(input_file, 'r', encoding=detected_encoding) as f:
        data = f.read()

    # Parse the JSON to ensure validity
    json_data = json.loads(data)

    # Write the cleaned JSON to a new file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=4)

    print(f"File successfully re-encoded and saved to {output_file}")

except Exception as e:
    print(f"Error processing file: {e}")
