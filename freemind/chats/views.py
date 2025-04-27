from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Message
from appointment.forms import MessageForm
from django.contrib.auth.decorators import login_required
from users.models import User, Profile, Therapist
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.template.loader import render_to_string

@login_required
def chat_view(request, username):
    other_user = User.objects.get(username=username)

    # Check if the user is a therapist or a patient
    therapist = None
    if request.user.role == 'therapist':
        # Fetch the therapist object only for therapists
        therapist = Therapist.objects.get(user=request.user)


    if request.user.role == 'patient':
       if request.user.profile.assigned_therapist_id != other_user.id:
        return HttpResponseForbidden("You are not matched with this therapist.")
    elif request.user.role == 'therapist':
        patient_profiles = Profile.objects.filter(assigned_therapist=therapist)
        if not patient_profiles.filter(user=other_user).exists():
            return HttpResponseForbidden("You are not matched with this patient.")

    # Mark received messages as read
    Message.objects.filter(sender=other_user, recipient=request.user, is_read=False).update(is_read=True)
    
    # Get the conversation between the user and the other user (patient or therapist)
    messages = Message.objects.filter(
        sender__in=[request.user, other_user],
        recipient__in=[request.user, other_user]
    ).order_by('timestamp')

    # Handle the message sending form
    form = MessageForm()
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.recipient = other_user
            msg.save()
            return redirect('chats:chat_view', username=username)

    return render(request, 'chats/message_list.html', {
        'messages': messages,
        'form': form,
        'other_user': other_user
    })

@login_required
def load_messages(request, username):
    other_user = User.objects.get(username=username)
    messages = Message.objects.filter(
        sender__in=[request.user, other_user],
        recipient__in=[request.user, other_user]
    )
    html = render_to_string('chats/partials/message_list.html', {'messages': messages})
    return JsonResponse({'html': html})

@login_required
def inbox_view(request):
    matched_users = []
    unread_counts = {}

    if request.user.role == 'patient':
        therapist = request.user.profile.assigned_therapist
        if therapist:
            matched_users = [therapist]
            count = Message.objects.filter(sender=therapist, recipient=request.user, is_read=False).count()
            unread_counts[therapist.username] = count
    elif request.user.role == 'therapist':
        patients = Profile.objects.filter(assigned_therapist=request.user)
        for profile in patients:
            matched_users.append(profile.user)
            count = Message.objects.filter(sender=profile.user, recipient=request.user, is_read=False).count()
            unread_counts[profile.user.username] = count

    return render(request, 'chats/inbox.html', {
        'matched_users': matched_users,
        'unread_counts': unread_counts,
    })


@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    
    if request.user != message.sender:
        return HttpResponseForbidden("You can only delete your own messages.")
    
    message.is_deleted = True
    message.save()
    
    message.delete()
    return JsonResponse({'status': 'deleted'})
