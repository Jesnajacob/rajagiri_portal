from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from accounts.decorators import role_required
from .models import Event, EventRegistration
from .forms import EventForm


def event_list(request):
    events = Event.objects.filter(date__gte=timezone.now())
    past_events = Event.objects.filter(date__lt=timezone.now())
    registered_ids = []
    if request.user.is_authenticated:
        registered_ids = list(EventRegistration.objects.filter(user=request.user).values_list("event_id", flat=True))
    return render(request, "events/list.html", {
        "events": events, "past_events": past_events, "registered_ids": registered_ids,
    })


def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    already_registered = False
    if request.user.is_authenticated:
        already_registered = EventRegistration.objects.filter(event=event, user=request.user).exists()
    return render(request, "events/detail.html", {"event": event, "already_registered": already_registered})


@login_required
def register_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not event.is_open():
        messages.error(request, "Registration is closed for this event.")
        return redirect("events:detail", pk=pk)
    _, created = EventRegistration.objects.get_or_create(event=event, user=request.user)
    if created:
        messages.success(request, f"Registered for {event.title}!")
    else:
        messages.info(request, "You are already registered for this event.")
    return redirect("events:detail", pk=pk)


@login_required
@role_required("faculty", "placement_officer", "rlabs_coordinator", "admin")
def event_create(request):
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, "Event created.")
            return redirect("events:list")
    else:
        form = EventForm()
    return render(request, "events/form.html", {"form": form, "title": "Create Event"})


@login_required
@role_required("faculty", "placement_officer", "rlabs_coordinator", "admin")
def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Event updated.")
            return redirect("events:list")
    else:
        form = EventForm(instance=event)
    return render(request, "events/form.html", {"form": form, "title": "Edit Event"})


@login_required
@role_required("faculty", "placement_officer", "rlabs_coordinator", "admin")
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        event.delete()
        messages.success(request, "Event deleted.")
        return redirect("events:list")
    return render(request, "placement/confirm_delete.html", {"object": event})
