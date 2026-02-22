import threading
import logging
from django.db import connection
from apps.brain.processor import APIDocumentProcessor
from apps.brain.models import ProcessingJob

logger = logging.getLogger(__name__)

class BackgroundProcessor:
    """
    Handles background processing of documents using Python threads.
    This allows the API to return immediately while processing continues.
    """
    
    @staticmethod
    def process_job_in_background(job_id):
        """
        Start a background thread to process the job
        """
        thread = threading.Thread(
            target=BackgroundProcessor._process_job_thread,
            args=(job_id,)
        )
        thread.daemon = True  # Thread will exit if main program exits
        thread.start()
        
    @staticmethod
    def _process_job_thread(job_id):
        """
        The actual processing logic running in the thread
        """
        # Close any old database connections to avoid "connection already closed" errors
        # in the new thread
        connection.close()
        
        try:
            logger.info(f"🧵 Starting background thread for Job {job_id}")
            
            # Re-fetch job to ensure we have fresh data
            try:
                job = ProcessingJob.objects.get(id=job_id)
            except ProcessingJob.DoesNotExist:
                logger.error(f"Job {job_id} not found in background thread")
                return

            # Initialize processor
            processor = APIDocumentProcessor(language=job.language)
            
            # Run the processing
            # This method handles status updates (processing -> completed/failed)
            # and saving Q&A pairs to the DB
            result = processor.process_with_job(job)
            
            if result['success']:
                logger.info(f"✅ Background processing successful for Job {job_id}")
            else:
                logger.error(f"❌ Background processing failed for Job {job_id}: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"💥 Critical error in background thread for Job {job_id}: {str(e)}")
            # Try to mark job as failed if possible
            try:
                job = ProcessingJob.objects.get(id=job_id)
                job.mark_failed(f"System error: {str(e)}")
            except Exception:
                pass
        finally:
            # Close DB connection for this thread
            connection.close()
