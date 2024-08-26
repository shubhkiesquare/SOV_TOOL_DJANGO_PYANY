import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_sample_data(output_file='search_results.csv'):
    np.random.seed(42)

    brands = ['BrandA', 'BrandB', 'BrandC']
    countries = ['USA', 'UK', 'Canada']
    time_slots = ['Early Morning', 'Morning', 'Mid-Day', 'Afternoon', 'Evening', 'Night', 'Late Night']
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 31)

    data = []
    current_date = start_date
    while current_date <= end_date:
        for brand in brands:
            for country in countries:
                for time_slot in time_slots:
                    day_type = 'Weekend' if current_date.weekday() >= 5 else 'Weekday'
                    share = np.random.uniform(5, 20)
                    data.append({
                        'Date': current_date.strftime('%Y-%m-%d'),
                        'Brand': brand,
                        'Country': country,
                        'Time_of_Day': time_slot,
                        'Day_Type': day_type,
                        'Share': round(share, 2)
                    })
        current_date += timedelta(days=1)

    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    print(f"Sample data saved to {output_file}")

if __name__ == "__main__":
    generate_sample_data()