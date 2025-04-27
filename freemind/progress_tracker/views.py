from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone  
from .models import MoodLog, PHQ9Response
import json
from datetime import timedelta

@login_required
@csrf_exempt
def log_mood(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mood_score = int(data['mood'])
            if not 1 <= mood_score <= 10:
                raise ValueError("Mood score must be between 1 and 10")
                
            MoodLog.objects.create(
                user=request.user,
                mood=mood_score
            )
            return JsonResponse({'status': 'success', 'message': 'Mood logged successfully'})
            
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'Failed to log mood'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
@csrf_exempt
def submit_phq9(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Validate all questions were answered
            if len(data) != 9 or any(v not in ['0', '1', '2', '3'] for v in data.values()):
                raise ValueError("All questions must be answered with valid values")
                
            score = sum(int(v) for v in data.values())
            
            PHQ9Response.objects.create(
                user=request.user,
                score=score,
                responses=data
            )
            
            return JsonResponse({
                'status': 'success',
                'score': score,
                'severity': get_phq9_severity(score),
                'message': 'PHQ-9 submitted successfully'
            })
            
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'Failed to submit survey'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_phq9_severity(score):
    if score < 5: return "Minimal depression"
    elif score < 10: return "Mild depression"
    elif score < 15: return "Moderate depression"
    elif score < 20: return "Moderately severe depression"
    else: return "Severe depression"

@login_required
def get_progress_data(request):
    try:
        date_threshold = timezone.now() - timedelta(days=30)  # <-- Changed here
        
        mood_logs = MoodLog.objects.filter(
            user=request.user,
            date__gte=date_threshold
        ).order_by('date')
        
        phq9_responses = PHQ9Response.objects.filter(
            user=request.user,
            date__gte=date_threshold
        ).order_by('date')
        
        mood_scores = [log.mood for log in mood_logs]
        phq9_scores = [response.score for response in phq9_responses]
        
        positive_days = 0
        if mood_scores:
            positive_days = round(
                sum(1 for score in mood_scores if score >= 7) / len(mood_scores) * 100
            )
        
        return JsonResponse({
            'status': 'success',
            'positive_days': positive_days,
            'needs_attention': 100 - positive_days,
            'mood_scores': mood_scores,
            'phq9_scores': phq9_scores
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
