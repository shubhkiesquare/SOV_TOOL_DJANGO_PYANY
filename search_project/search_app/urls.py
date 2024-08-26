

from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.search_view, name='search'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('results/<int:search_query_id>/', views.results_view, name='results'),
    path('upload/', views.upload_csv, name='upload_csv'),
    path('analysis/', views.sov_analysis, name='sov_analysis'),
    path('trend/', views.sov_trend, name='sov_trend'),
    path('geography/', views.geographic_trend, name='geographic_trend'),
    path('core-vs-non-core/', views.core_vs_non_core_sov, name='core_vs_non_core_sov'),
    path('top-10-kw-paid-sov/', views.top_10_kw_paid_sov, name='top_10_kw_paid_sov'),
    path('paid-vs-organic/', views.paid_vs_organic_rank, name='paid_vs_organic_rank'),
    path('top-keyword-analysis/', views.top_keyword_analysis, name='top_keyword_analysis')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)