from celery import shared_task
from django.utils import timezone
from .models import SearchQuery, SearchResult
from .utils import process_search_query
import logging

logger = logging.getLogger(__name__)

@shared_task
def schedule_search(search_query_id):
    search_query = SearchQuery.objects.get(id=search_query_id)
    perform_scheduled_search.apply_async(args=[search_query_id], eta=search_query.start_date)
    logger.info(f"Initial search scheduled for query ID: {search_query_id} at {search_query.start_date}")

@shared_task
def perform_scheduled_search(search_query_id):
    search_query = SearchQuery.objects.get(id=search_query_id)
    current_time = timezone.now()
    
    if search_query.start_date <= current_time <= search_query.end_date:
        logger.info(f"Performing scheduled search for query ID: {search_query_id}")
        results = process_search_query(search_query)
        for result in results:
            SearchResult.objects.create(search_query=search_query, **result)
        logger.info(f"Completed scheduled search for query ID: {search_query_id}")
        
        next_run = current_time + timezone.timedelta(minutes=5)
        if next_run <= search_query.end_date:
            perform_scheduled_search.apply_async(args=[search_query_id], eta=next_run)
            logger.info(f"Scheduled next search for query ID: {search_query_id} at {next_run}")
    else:
        logger.info(f"Search period ended for query ID: {search_query_id}")