# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import MoodLog, PHQ9Response
import json

@login_required
@csrf_exempt
def log_mood(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        MoodLog.objects.create(
            user=request.user,
            mood=data['mood']
        )
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@csrf_exempt
def submit_phq9(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        score = sum(data.values())
        PHQ9Response.objects.create(
            user=request.user,
            score=score
        )
        return JsonResponse({'score': score})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def get_progress_data(request):
    mood_logs = MoodLog.objects.filter(user=request.user).order_by('date')
    phq9_responses = PHQ9Response.objects.filter(user=request.user).order_by('date')
    
    return JsonResponse({
        'dates': [log.date.strftime('%Y-%m-%d') for log in mood_logs],
        'mood_scores': [log.mood for log in mood_logs],
        'phq9_scores': [response.score for response in phq9_responses]
    })

