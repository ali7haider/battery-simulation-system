import random
import pandas as pd
data = {
    "Time": [f"00:{str(i).zfill(2)}" for i in range(60)],  # 60 seconds of data
    "Power": [random.randint(-1000, 1000) for _ in range(60)]  # Random power values between -1000W and 1000W
}

# Create DataFrame
df = pd.DataFrame(data)

# Save to CSV
csv_filename = "dummy_power_data.csv"
df.to_csv(csv_filename, index=False)

print(f"Dummy CSV file '{csv_filename}' generated successfully!")
