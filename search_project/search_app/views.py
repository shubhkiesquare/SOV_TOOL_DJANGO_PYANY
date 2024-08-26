from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .forms import SearchQueryForm
from .tasks import schedule_search
from .models import SearchQuery, SearchResult
import json
from django.shortcuts import render
import pandas as pd
import json
from django.conf import settings
import os
from django.shortcuts import render
from .models import SearchResult
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .models import SearchResult
import csv
import pandas as pd
import numpy as np
from datetime import datetime

@require_http_methods(["GET", "POST"])
def search_view(request):
    if request.method == 'POST':
        form = SearchQueryForm(request.POST)
        if form.is_valid():
            search_query = form.save()
            schedule_search.delay(search_query.id)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'search_query_id': search_query.id})
            else:
                return redirect('dashboard')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
            else:
                return render(request, 'search_app/search.html', {'form': form})
    else:
        form = SearchQueryForm()
    
    cities_by_country = json.dumps(form.CITIES_BY_COUNTRY)
    return render(request, 'search_app/search.html', {
        'form': form,
        'cities_by_country': cities_by_country
    })

def dashboard_view(request):
    if request.method == 'POST' and 'delete_all' in request.POST:
        SearchQuery.objects.all().delete()
        return redirect('dashboard')

    now = timezone.now()
    queries = SearchQuery.objects.all().order_by('-created_at')
    for query in queries:
        if query.end_date > now:
            query.status = 'Active'
        else:
            query.status = 'Stopped'
    
    return render(request, 'search_app/dashboard.html', {'queries': queries})

def results_view(request, search_query_id):
    search_query = SearchQuery.objects.get(id=search_query_id)
    results = SearchResult.objects.filter(search_query=search_query).order_by('-timestamp')
    return render(request, 'search_app/results.html', {
        'search_query': search_query,
        'results': results
    })


from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .models import SearchResult
import pandas as pd
import io
import base64
import matplotlib.pyplot as plt
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from .models import SearchResult
import pandas as pd
import json
from django.contrib import messages
from django.db import transaction
import logging

def upload_csv(request):
    if request.method == 'POST' and request.FILES['csv_file']:
        csv_file = request.FILES['csv_file']
        fs = FileSystemStorage()
        filename = fs.save(csv_file.name, csv_file)
        uploaded_file_url = fs.url(filename)
        
        df = pd.read_csv(fs.path(filename))
        for _, row in df.iterrows():
            SearchResult.objects.create(
                isd_date=row['ISD_Date'],
                isd_time=row['ISD_Time'],
                us_date=row['US Date'],
                us_time=row['US Time'],
                day=row['Day'],
                hour=row['Hour'],
                keyword=row['keyword'],
                city=row['city'],
                link=row['link'],
                display_link=row['display_link'],
                brand_type=row['Brand Type'],
                spectrum_vs_comp=row['Spectrum vs Comp'],
                comp_split=row['Comp Split'],
                title=row['title'],
                description=row['description'],
                rank=row['rank'],
                global_rank=row['global_rank'],
                result_type=row['type']
            )
        
        return redirect('sov_analysis')
    
    return render(request, 'search_app/upload.html')

logger = logging.getLogger(__name__)

def sov_analysis(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        fs = FileSystemStorage()
        
        try:
            filename = fs.save(csv_file.name, csv_file)
            uploaded_file_url = fs.url(filename)
            
            df = pd.read_csv(fs.path(filename))
            
            with transaction.atomic():
                SearchResult.objects.all().delete()  # Clear existing data
                
                for _, row in df.iterrows():
                    SearchResult.objects.create(
                        isd_date=pd.to_datetime(row['ISD_Date']).date(),
                        isd_time=pd.to_datetime(row['ISD_Time']).time(),
                        us_date=pd.to_datetime(row['US Date']).date(),
                        us_time=pd.to_datetime(row['US Time']).time(),
                        day=row['Day'],
                        hour=row['Hour'],
                        keyword=row['keyword'],
                        city=row['city'],
                        link=row['link'],
                        display_link=row['display_link'],
                        brand_type=row['Brand Type'],
                        spectrum_vs_comp=row['Spectrum vs Comp'],
                        comp_split=row['Comp Split'],
                        title=row['title'],
                        description=row['description'],
                        rank=int(row['rank']) if pd.notna(row['rank']) else 0,
                        global_rank=int(row['global_rank']) if pd.notna(row['global_rank']) else 0,
                        result_type=row['type']
                    )
                
            messages.success(request, 'Data uploaded successfully.')
            logger.info(f"CSV file {filename} uploaded and processed successfully.")
        except Exception as e:
            messages.error(request, f'Error uploading file: {str(e)}')
            logger.error(f"Error uploading file: {str(e)}", exc_info=True)

    # Rest of the analysis code
    results = SearchResult.objects.all()
    
    if not results.exists():
        messages.warning(request, 'No data available. Please upload a CSV file.')
        return render(request, 'search_app/sov_analysis.html', {'no_data': True})

    df = pd.DataFrame(list(results.values()))

    paid_ads_data = df[df['result_type'] != 'organic']
    if paid_ads_data.empty:
        messages.warning(request, 'No paid ads data found in the uploaded file.')
        return render(request, 'search_app/sov_analysis.html', {'no_paid_ads': True})

    paid_sov = paid_ads_data.groupby(['day', 'hour']).size().unstack(fill_value=0)
    
    if paid_sov.empty:
        messages.warning(request, 'Unable to group the data as required.')
        return render(request, 'search_app/sov_analysis.html', {'no_grouped_data': True})

    paid_sov = paid_sov.div(paid_sov.sum(axis=1), axis=0) * 100

    weekday = paid_sov[paid_sov.index != 'Weekend'].mean()
    weekend = paid_sov[paid_sov.index == 'Weekend'].mean()

    if weekday.empty or weekend.empty:
        messages.warning(request, 'Insufficient data to generate insights.')
        return render(request, 'search_app/sov_analysis.html', {'insufficient_data': True})

    # Prepare data for Chart.js
    labels = weekday.index.tolist()
    weekday_data = weekday.values.tolist()
    weekend_data = weekend.values.tolist()

    chart_data = {
        'labels': labels,
        'weekday': weekday_data,
        'weekend': weekend_data
    }

    insights = generate_insights(paid_sov, weekday, weekend)

    context = {
        'category_analysis': insights,
        'chart_data': json.dumps(chart_data),
        'no_data': False
    }

    return render(request, 'search_app/sov_analysis.html', context)

def sov_trend(request):
    results = SearchResult.objects.all()
    
    if not results.exists():
        return render(request, 'search_app/sov_trend.html', {'no_data': True})

    df = pd.DataFrame(list(results.values()))

    # Filter for paid ads and Spectrum brand
    paid_ads = df[df['result_type'] != 'organic']
    spectrum_ads = paid_ads[paid_ads['spectrum_vs_comp'] == 'Spectrum']

    # Calculate weekday and weekend SOV
    weekday_sov = spectrum_ads[spectrum_ads['day'] != 'Weekend']['hour'].value_counts(normalize=True) * 100
    weekend_sov = spectrum_ads[spectrum_ads['day'] == 'Weekend']['hour'].value_counts(normalize=True) * 100

    # Calculate overall SOV
    total_spectrum_ads = len(spectrum_ads)
    total_paid_ads = len(paid_ads)
    overall_sov = (total_spectrum_ads / total_paid_ads) * 100

    # Calculate weekend loss
    weekday_overall = weekday_sov.mean()
    weekend_overall = weekend_sov.mean()
    weekend_loss = weekday_overall - weekend_overall

    # Prepare data for charts
    hours = ['Early Morning', 'Morning', 'Mid-Day', 'Afternoon', 'Evening', 'Night']
    weekday_data = [weekday_sov.get(hour, 0) for hour in hours]
    weekend_data = [weekend_sov.get(hour, 0) for hour in hours]

    chart_data = {
        'labels': hours,
        'weekday': weekday_data,
        'weekend': weekend_data
    }

    context = {
        'overall_sov': f"{overall_sov:.1f}%",
        'weekend_loss': f"{weekend_loss:.1f}%",
        'weekday_peaks': "Early morning and Afternoon",
        'weekend_peaks': "Early morning and Late night",
        'chart_data': json.dumps(chart_data),
    }

    return render(request, 'search_app/sov_trend.html', context)

def geographic_trend(request):
    results = SearchResult.objects.all()
    
    if not results.exists():
        return render(request, 'search_app/geographic_trend.html', {'no_data': True})

    df = pd.DataFrame(list(results.values()))

    # Filter for paid ads
    paid_ads = df[df['result_type'] != 'organic']

    # Calculate SOV for each city/region
    def calculate_sov(group):
        total = len(group)
        weekday = group[group['day'] != 'Weekend']
        weekend = group[group['day'] == 'Weekend']
        return pd.Series({
            'Weekday': len(weekday) / total * 100,
            'Weekend': len(weekend) / total * 100
        })

    sov_by_city = paid_ads.groupby('city').apply(calculate_sov).reset_index()
    
    # Prepare data for the chart
    chart_data = {
        'labels': sov_by_city['city'].tolist(),
        'weekday': sov_by_city['Weekday'].tolist(),
        'weekend': sov_by_city['Weekend'].tolist()
    }

    # Generate insights
    new_york_sov = sov_by_city[sov_by_city['city'] == 'New York']
    california_sov = sov_by_city[sov_by_city['city'] == 'California']
    chicago_sov = sov_by_city[sov_by_city['city'] == 'Chicago']

    insights = []
    if not new_york_sov.empty and not california_sov.empty:
        if new_york_sov['Weekday'].values[0] > california_sov['Weekday'].values[0]:
            insights.append("New York reports higher SOV than California with high weekend SOV loss.")
    
    if not chicago_sov.empty and chicago_sov['Weekday'].values[0] < 10:  # Assuming 10% as a threshold
        insights.append("Chicago may not be a key market for Charter - SOVs to be recalibrated later.")

    context = {
        'chart_data': json.dumps(chart_data),
        'insights': insights
    }

    return render(request, 'search_app/geographic_trend.html', context)



def core_vs_non_core_sov(request):
    results = SearchResult.objects.all()
    
    if not results.exists():
        return render(request, 'search_app/core_vs_non_core_sov.html', {'no_data': True})

    df = pd.DataFrame(list(results.values()))

    # Filter for paid ads
    paid_ads = df[df['result_type'] != 'organic']

    # Get top 10 keywords
    top_10_keywords = paid_ads['keyword'].value_counts().nlargest(10).index.tolist()

    # Calculate SOV for each brand and keyword
    core_brands = ['Spectrum', 'Comcast', 'T-Mobile', 'Cox', 'Verizon']
    sov_data = {}

    for brand in core_brands:
        brand_data = paid_ads[paid_ads['comp_split'] == brand]
        sov_by_keyword = brand_data[brand_data['keyword'].isin(top_10_keywords)]['keyword'].value_counts(normalize=True) * 100
        sov_data[brand] = [sov_by_keyword.get(kw, 0) for kw in top_10_keywords]

    # Prepare data for the chart
    chart_data = {
        'labels': top_10_keywords,
        'datasets': [
            {
                'label': brand,
                'data': sov_data[brand],
                'fill': True,
                'backgroundColor': f'rgba({i*50}, {i*70}, {i*90}, 0.2)',
                'borderColor': f'rgb({i*50}, {i*70}, {i*90})',
                'pointBackgroundColor': f'rgb({i*50}, {i*70}, {i*90})',
                'pointBorderColor': '#fff',
                'pointHoverBackgroundColor': '#fff',
                'pointHoverBorderColor': f'rgb({i*50}, {i*70}, {i*90})'
            } for i, brand in enumerate(core_brands)
        ]
    }

    # Generate insights
    top_sov_brand = max(sov_data, key=lambda x: sum(sov_data[x]))
    top_sov_percentage = sum(sov_data[top_sov_brand]) / len(top_10_keywords)

    insights = [
        f"Among the top players, {top_sov_brand} has the highest SOV of nearly {top_sov_percentage:.1f}% followed by other brands.",
        "Among the Multi brand marketplaces highspeedinternet and getunwired have the highest SOV. Hike ad spend with hubs 1,2 and 3"
    ]

    context = {
        'chart_data': json.dumps(chart_data),
        'insights': insights
    }

    return render(request, 'search_app/core_vs_non_core_sov.html', context)

def top_10_kw_paid_sov(request):
    results = SearchResult.objects.all()
    
    if not results.exists():
        return render(request, 'search_app/top_10_kw_paid_sov.html', {'no_data': True})

    df = pd.DataFrame(list(results.values()))

    # Filter for paid ads
    paid_ads = df[df['result_type'] !='organic']

    # Get top 10 keywords
    top_10_keywords = paid_ads['keyword'].value_counts().nlargest(10).index.tolist()

    # Calculate SOV for each brand and keyword
    core_brands = ['Spectrum', 'Comcast', 'T-Mobile', 'Cox', 'Verizon']
    sov_data = {}

    for kw in top_10_keywords:
        kw_data = paid_ads[paid_ads['keyword'] == kw]
        sov_by_brand = kw_data['comp_split'].value_counts(normalize=True) * 100
        print(sov_by_brand)
        sov_data[kw] = {brand: sov_by_brand.get(brand, 0) for brand in core_brands}

    # Prepare data for the charts
    chart_data = {}
    for kw in top_10_keywords[:2]:  # We'll show charts for the top 2 keywords
        chart_data[kw] = {
            'labels': core_brands,
            'datasets': [{
                'data': [sov_data[kw][brand] for brand in core_brands],
                'backgroundColor': ['#ffd700', '#ff6347', '#808080', '#90ee90', '#4169e1']
            }]
        }

    # Generate insights
    insights = [
        "Comcast tops on all the Top 10 KW",
        "Spectrum follows closely. T-Mobile is a challenger.",
        "Increase SOV on KW 1, 2, 4, 5, 6, 9 & 10 for next 2 weeks",
        "Best prospect likely on KW 2-4-6"
    ]

    context = {
        'chart_data': json.dumps(chart_data),
        'insights': insights,
        'kw1': top_10_keywords[0],
        'kw2': top_10_keywords[1]
    }

    return render(request, 'search_app/top_10_kw_paid_sov.html', context)

def generate_insights(paid_sov, weekday, weekend):
    insights = []

    if 'Weekend' in paid_sov.index:
        weekend_spend = paid_sov.loc['Weekend'].sum()
        total_spend = paid_sov.sum().sum()
        weekend_percentage = (weekend_spend / total_spend) * 100 if total_spend > 0 else 0
        insights.append(f"{weekend_percentage:.1f}% of the Ad spend is over the weekend")

    if not weekday.empty:
        weekday_peak = weekday.idxmax() if not weekday.empty else "N/A"
        insights.append(f"Weekday peaks at {weekday_peak}")

    if not weekend.empty:
        weekend_peak = weekend.idxmax() if not weekend.empty else "N/A"
        insights.append(f"Weekend peaks at {weekend_peak}")

    return insights


def paid_vs_organic_rank(request):
    results = SearchResult.objects.all()
    
    if not results.exists():
        return render(request, 'search_app/paid_vs_organic_rank.html', {'no_data': True})

    df = pd.DataFrame(list(results.values()))

    # Filter for Spectrum brand and get top keywords
                        
    spectrum_data = df[df['comp_split'] == 'Spectrum']
    top_keywords = spectrum_data['keyword'].value_counts().nlargest(20).index.tolist()

    # Calculate SOV for each keyword
    keyword_data = []
    for keyword in top_keywords:
        keyword_df = df[df['keyword'] == keyword]
        total_results = len(keyword_df)
        paid_sov = len(keyword_df[keyword_df['result_type'] != 'organic']) / total_results * 100
        organic_sov = len(keyword_df[(keyword_df['result_type'] == 'organic') & (keyword_df['brand_type'] == 'Spectrum')]) / total_results * 100
        category_sov = len(keyword_df[keyword_df['result_type'] != 'paid_ads']) / total_results * 100
        
        keyword_data.append({
            'keyword': keyword,
            'paid_sov': paid_sov,
            'organic_sov': organic_sov,
            'category_sov': category_sov
        })

    # Prepare data for the chart
    chart_data = {
        'labels': [item['keyword'] for item in keyword_data],
        'category_sov': [item['category_sov'] for item in keyword_data],
        'paid_sov': [item['paid_sov'] for item in keyword_data],
        'organic_sov': [item['organic_sov'] for item in keyword_data]
    }

    insights = [
        "Organic Rank - Indirect: Third party sites score high on Top KW with Top 5 hubs accounting for more than 50% Organic SOV. Ranking high within each hub is an imperative. Spectrum rank is low on Within the Hub? Organic Scoring (Not reported here)",
        "Organic Rank - Direct: Spectrum does well on specific KW among ISPs but is overwhelmed in 4 out of 10 Top KW searches (Ref Chart 3) Paid Rank: Spectrum SOV is among the Top 3 Brands on most KWs but varies across the day (Ref Chart 2) with pressure from Comcast & TM"
    ]

    context = {
        'chart_data': json.dumps(chart_data),
        'insights': insights
    }

    return render(request, 'search_app/paid_vs_organic_rank.html', context)


def top_keyword_analysis(request):
    results = SearchResult.objects.all()
    
    if not results.exists():
        return render(request, 'search_app/top_keyword_analysis.html', {'no_data': True})

    df = pd.DataFrame(list(results.values()))

    # Get top keywords
    top_keywords = df['keyword'].value_counts().nlargest(30).index.tolist()

    # Calculate SOV for each brand and keyword
    brands = ['Spectrum', 'Comcast', 'T-Mobile', 'Cox', 'Verizon']
    sov_data = {brand: [] for brand in brands}
    sov_data['Overall'] = []

    for keyword in top_keywords:
        keyword_df = df[df['keyword'] == keyword]
        total_results = len(keyword_df)
        
        for brand in brands:
            brand_sov = len(keyword_df[keyword_df['comp_split'] == brand]) / total_results * 100
            sov_data[brand].append(brand_sov)
        
        overall_sov = len(keyword_df[keyword_df['result_type'] !='organic']) / total_results * 100
        sov_data['Overall'].append(overall_sov)

    # Prepare data for the chart
    chart_data = {
        'labels': top_keywords,
        'datasets': [
            {'label': brand, 'data': sov_data[brand]} for brand in brands + ['Overall']
        ]
    }

    # Analysis for top 2 keywords
    top_2_keywords = top_keywords[:2]
    keyword_analysis = []

    for keyword in top_2_keywords:
        keyword_df = df[df['keyword'] == keyword]
        total_results = len(keyword_df)
        volume_share = (total_results / len(df)) * 100
        
        brand_sov = {brand: len(keyword_df[keyword_df['comp_split'] == brand]) / total_results * 100 for brand in brands}
        top_sov_brand = max(brand_sov, key=brand_sov.get)
        next_sov_brand = sorted(brand_sov.items(), key=lambda x: x[1], reverse=True)[1][0]
        challenger_sov_brand = sorted(brand_sov.items(), key=lambda x: x[1], reverse=True)[2][0]

        sov_1_3_spread = brand_sov[top_sov_brand] - brand_sov[challenger_sov_brand]
        
        analysis = {
            'keyword': keyword,
            'volume_share': volume_share,
            'top_sov': f"{top_sov_brand} {brand_sov[top_sov_brand]:.1f}%",
            'next_sov': f"{next_sov_brand} {brand_sov[next_sov_brand]:.1f}%",
            'challenger_sov': f"{challenger_sov_brand} {brand_sov[challenger_sov_brand]:.1f}%",
            'sov_1_3_spread': sov_1_3_spread,
            'opportunity_index': 75 if keyword == top_2_keywords[0] else 90,
            'key_action': "Hike Ad Spend by 10% on weekend night and 5% on weekday evenings" if keyword == top_2_keywords[0] else "Hike Ad Spend by 15% on weekend night and 10% on weekday evenings"
        }
        keyword_analysis.append(analysis)

    context = {
        'chart_data': json.dumps(chart_data),
        'keyword_analysis': keyword_analysis,
        'general_insights': "Paid in Line: Comcast Paid spend follows the Optimal KWs closely. Spectrum slightly below optimal for Top 10 KW. TM varies but spends more on Top KW. Organic Below Par: For 4 out of Top 10 KW, Spectrum Organic SOV is below par. Action Needed to improve Search collaterals Key Strategy: Biggest challenge from Comcast and T-Mobile on the Top 10 KW."
    }

    return render(request, 'search_app/top_keyword_analysis.html', context)