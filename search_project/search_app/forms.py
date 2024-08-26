from django import forms
from django.utils import timezone
from .models import SearchQuery

class SearchQueryForm(forms.ModelForm):
    PAGINATION_CHOICES = [
        ('', 'None'),
        ('10', '10 results'),
        ('20', '20 results'),
        ('50', '50 results'),
    ]

    CITIES_BY_COUNTRY = {
        'US': [
            ('New York,New York,United States', 'New York'),
            ('Los Angeles,California,United States', 'Los Angeles'),
            ('Chicago,Illinois,United States', 'Chicago'),
            ('Houston,Texas,United States', 'Houston'),
            ('Phoenix,Arizona,United States', 'Phoenix'),
        ],
        'GB': [
            ('London,England,United Kingdom', 'London'),
            ('Manchester,England,United Kingdom', 'Manchester'),
            ('Birmingham,England,United Kingdom', 'Birmingham'),
            ('Glasgow,Scotland,United Kingdom', 'Glasgow'),
            ('Liverpool,England,United Kingdom', 'Liverpool'),
        ],
        'CA': [
            ('Toronto,Ontario,Canada', 'Toronto'),
            ('Montreal,Quebec,Canada', 'Montreal'),
            ('Vancouver,British Columbia,Canada', 'Vancouver'),
            ('Calgary,Alberta,Canada', 'Calgary'),
            ('Ottawa,Ontario,Canada', 'Ottawa'),
        ],
        'AU': [
            ('Sydney,New South Wales,Australia', 'Sydney'),
            ('Melbourne,Victoria,Australia', 'Melbourne'),
            ('Brisbane,Queensland,Australia', 'Brisbane'),
            ('Perth,Western Australia,Australia', 'Perth'),
            ('Adelaide,South Australia,Australia', 'Adelaide'),
        ],
        'IN': [
            ('Mumbai,Maharashtra,India', 'Mumbai'),
            ('Delhi,Delhi,India', 'Delhi'),
            ('Bangalore,Karnataka,India', 'Bangalore'),
            ('Kolkata,West Bengal,India', 'Kolkata'),
            ('Chennai,Tamil Nadu,India', 'Chennai'),
        ],
    }

    city = forms.ChoiceField(choices=[], required=False)
    pagination = forms.ChoiceField(choices=PAGINATION_CHOICES, required=False)

    class Meta:
        model = SearchQuery
        fields = ['search_engine', 'country', 'city', 'pagination', 'device', 'keywords', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_date'].initial = timezone.now()
        self.fields['end_date'].initial = timezone.now() + timezone.timedelta(days=7)
        
        # Set choices for city field based on the selected country
        country = self.data.get('country') or self.initial.get('country')
        if country:
            self.fields['city'].choices = self.CITIES_BY_COUNTRY.get(country, [])

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        keywords = cleaned_data.get('keywords')

        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError("End date should be after start date.")

        if keywords:
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
            if len(keyword_list) < 3 or len(keyword_list) > 20:
                raise forms.ValidationError("Please enter between 3 and 20 keywords.")

        return cleaned_data